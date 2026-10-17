// GPU renderer for the evolution animation. Every triangle's whole journey from
// one stage to the next is worked out in the vertex shader, so tens of thousands
// of them cost the page almost nothing per frame.
//
// Changes overlap: the next one sets off before the last has quite landed, so
// two are drawn at once, each from its own buffer, and every triangle is drawn
// by the one it is in. Each triangle is one instance with five vec4
// attributes, written by the planner in evolution.js:
//   from, to  x, y (units from the centre, or radius and angle for dust), height, dust flag
//   look      size from, size to, colour from, colour to (palette indices)
//   more      resting angle from, resting angle to, seed, unused
//   time      sets off, lands, shown from (seconds from the change's start), unused

const VERTEX = `#version 300 es
precision highp float;

in vec4 a_from;
in vec4 a_to;
in vec4 a_look;
in vec4 a_more;
in vec4 a_time;

uniform float u_time;      // seconds since this change began
uniform float u_retired;   // 1 once a newer change has begun: then a triangle shows here only until it lands
uniform float u_clock;     // seconds, for everything that keeps moving
uniform float u_step;      // seconds since the previous frame
uniform float u_ramp;      // share of a flight spent speeding up, and again slowing down
uniform float u_swirl;     // units of swirl in mid flight
uniform float u_breath;    // units of drift at rest
uniform float u_ripple;    // units a slow ripple moves every form by
uniform float u_freq;      // swirl features per unit
uniform float u_twist;     // radians the whole form spirals about the centre in mid change
uniform float u_spin;      // radians per second the dust turns
uniform float u_yaw;       // radians the form turns about its vertical axis
uniform float u_depth;     // units a form's full height stands out of the page
uniform vec2 u_centre;     // CSS px
uniform vec2 u_view;       // CSS px
uniform float u_scale;     // CSS px per unit
uniform float u_size;      // triangle circumradius, CSS px
uniform vec3 u_palette[8];

out vec4 v_colour;

// 3D simplex noise by Ian McEwan and Stefan Gustavson (MIT licence).
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 permute(vec4 x) { return mod289(((x * 34.0) + 10.0) * x); }
vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

float snoise(vec3 v) {
  const vec2 C = vec2(1.0 / 6.0, 1.0 / 3.0);
  const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
  vec3 i = floor(v + dot(v, C.yyy));
  vec3 x0 = v - i + dot(i, C.xxx);
  vec3 g = step(x0.yzx, x0.xyz);
  vec3 l = 1.0 - g;
  vec3 i1 = min(g.xyz, l.zxy);
  vec3 i2 = max(g.xyz, l.zxy);
  vec3 x1 = x0 - i1 + C.xxx;
  vec3 x2 = x0 - i2 + C.yyy;
  vec3 x3 = x0 - D.yyy;
  i = mod289(i);
  vec4 p = permute(permute(permute(
    i.z + vec4(0.0, i1.z, i2.z, 1.0)) +
    i.y + vec4(0.0, i1.y, i2.y, 1.0)) +
    i.x + vec4(0.0, i1.x, i2.x, 1.0));
  float n_ = 0.142857142857;
  vec3 ns = n_ * D.wyz - D.xzx;
  vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7.0 * x_);
  vec4 x = x_ * ns.x + ns.yyyy;
  vec4 y = y_ * ns.x + ns.yyyy;
  vec4 h = 1.0 - abs(x) - abs(y);
  vec4 b0 = vec4(x.xy, y.xy);
  vec4 b1 = vec4(x.zw, y.zw);
  vec4 s0 = floor(b0) * 2.0 + 1.0;
  vec4 s1 = floor(b1) * 2.0 + 1.0;
  vec4 sh = -step(h, vec4(0.0));
  vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy;
  vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;
  vec3 p0 = vec3(a0.xy, h.x);
  vec3 p1 = vec3(a0.zw, h.y);
  vec3 p2 = vec3(a1.xy, h.z);
  vec3 p3 = vec3(a1.zw, h.w);
  vec4 norm = taylorInvSqrt(vec4(dot(p0, p0), dot(p1, p1), dot(p2, p2), dot(p3, p3)));
  p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
  vec4 m = max(0.5 - vec4(dot(x0, x0), dot(x1, x1), dot(x2, x2), dot(x3, x3)), 0.0);
  m = m * m;
  return 105.0 * dot(m * m, vec4(dot(p0, x0), dot(p1, x1), dot(p2, x2), dot(p3, x3)));
}

// Divergence-free flow from the noise: what makes the motion read as fluid.
vec2 curl(vec2 p, float z) {
  const float e = 0.02;
  float a = snoise(vec3(p.x, p.y + e, z)), b = snoise(vec3(p.x, p.y - e, z));
  float c = snoise(vec3(p.x + e, p.y, z)), d = snoise(vec3(p.x - e, p.y, z));
  return vec2(a - b, d - c) / (2.0 * e);
}

// Forms stay put; dust keeps slowly orbiting the centre.
vec2 place(vec4 p, float clock) {
  if (p.w < 0.5) return p.xy;
  float a = p.y + u_spin * clock;
  return vec2(cos(a), sin(a)) * p.x;
}

const float PI = 3.14159265;
const float TAU = 6.28318530718;

// How far through its flight the triangle is at a moment of the change.
float flight(float local) {
  return clamp((local - a_time.x) / max(a_time.y - a_time.x, 0.001), 0.0, 1.0);
}

// Speeds up, cruises and slows down again: no long crawl at either end.
float ease(float u) {
  float a = u_ramp, v = 1.0 / (1.0 - a);
  if (u < a) return v * u * u / (2.0 * a);
  if (u > 1.0 - a) return 1.0 - v * (1.0 - u) * (1.0 - u) / (2.0 * a);
  return v * (u - a * 0.5);
}

// Where the triangle is (units from the centre, plus height) at a moment of the change.
vec3 at(float local, float clock) {
  float u = flight(local), e = ease(u);
  vec2 p = mix(place(a_from, clock), place(a_to, clock), e);
  float h = mix(a_from.z, a_to.z, e);
  float mid = sin(PI * u);
  p += curl(p * u_freq, clock * 0.08) * (u_breath + u_swirl * mid);
  // a slow ripple runs through every form, so even a finished one never stands still
  p += vec2(sin(p.y * 0.11 + clock * 1.3), sin(p.x * 0.13 - clock * 1.1)) * u_ripple;
  // the middle turns further than the rim, so the change spirals like a galaxy
  float a = u_twist * mid / (1.0 + dot(p, p) / 3600.0);
  p = mat2(cos(a), sin(a), -sin(a), cos(a)) * p;
  return vec3(p, h);
}

void main() {
  // Each triangle shows in the change it is in: from when it landed in the
  // change before, and, once a newer change has begun, until it lands here.
  if (u_time < a_time.z || (u_retired > 0.5 && u_time >= a_time.y)) {
    gl_Position = vec4(0.0, 0.0, 2.0, 1.0); // outside the view, so nothing is drawn
    v_colour = vec4(0.0);
    return;
  }
  float e = ease(flight(u_time));
  vec3 p = at(u_time, u_clock);
  vec3 q = at(u_time - u_step, u_clock - u_step);

  // Moving triangles point where they are going; resting ones turn to their stage's angle.
  vec2 v = (p.xy - q.xy) * u_scale;
  float rest = a_more.x + (mod(a_more.y - a_more.x + PI, TAU) - PI) * e;
  float heading = atan(v.y, v.x);
  float w = smoothstep(0.12, 0.7, length(v));
  float angle = rest + (mod(heading - rest + PI, TAU) - PI) * w;

  // A gentle turn in depth: heights shift against the flat outline, dust drifts in parallax.
  float dust = mix(a_from.w, a_to.w, e);
  float z = p.z * u_depth;
  float cy = cos(u_yaw), sy = sin(u_yaw);
  vec3 r = vec3(p.x * cy + z * sy, p.y, -p.x * sy + z * cy);
  float near = 600.0 / (600.0 - r.z);

  float size = mix(a_look.x, a_look.y, e) * near;
  float twinkle = 0.65 + 0.35 * sin(u_clock * (1.3 + a_more.z * 1.7) + a_more.z * TAU);
  size *= mix(1.0, twinkle, dust);

  float k = float(gl_VertexID);
  vec2 corner = vec2(cos(angle + k * TAU / 3.0), sin(angle + k * TAU / 3.0)) * u_size * size;
  vec2 px = u_centre + r.xy * near * u_scale + corner;
  gl_Position = vec4(px / u_view * 2.0 - 1.0, 0.0, 1.0) * vec4(1.0, -1.0, 1.0, 1.0);

  vec3 colour = mix(u_palette[int(a_look.z)], u_palette[int(a_look.w)], e);
  v_colour = vec4(colour, mix(1.0, 0.55 + 0.35 * twinkle, dust));
}`;

const FRAGMENT = `#version 300 es
precision mediump float;
in vec4 v_colour;
out vec4 colour;
void main() {
  colour = vec4(v_colour.rgb * v_colour.a, v_colour.a);
}`;

const ATTRIBUTES = ['a_from', 'a_to', 'a_look', 'a_more', 'a_time'];
const STRIDE = ATTRIBUTES.length * 16; // bytes per triangle

// Returns a renderer for a WebGL2 context. Its shaders build in the
// background where the browser allows it (KHR_parallel_shader_compile), so
// the page never waits on them: `ready` turns true once they are built, and
// `failed` if they won't build, in which case the caller draws in 2D instead.
export function createRenderer(gl, palette) {
  const parallel = gl.getExtension('KHR_parallel_shader_compile');
  const program = gl.createProgram();
  const shaders = [[gl.VERTEX_SHADER, VERTEX], [gl.FRAGMENT_SHADER, FRAGMENT]].map(([type, source]) => {
    const shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    gl.attachShader(program, shader);
    return shader;
  });
  gl.linkProgram(program);

  let state = 'building';
  const uniform = {};
  const slots = []; // two buffers, one per change being drawn

  // Once built: look up the inputs and set what stays the same.
  function finish() {
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      const log = [gl.getProgramInfoLog(program), ...shaders.map((sh) => gl.getShaderInfoLog(sh))].filter(Boolean).join('\n');
      console.warn('Evolution animation: falling back to 2D drawing.', log);
      state = 'failed';
      return;
    }
    for (let i = 0, n = gl.getProgramParameter(program, gl.ACTIVE_UNIFORMS); i < n; i++) {
      const name = gl.getActiveUniform(program, i).name.replace('[0]', '');
      uniform[name] = gl.getUniformLocation(program, name);
    }
    for (let k = 0; k < 2; k++) {
      const vao = gl.createVertexArray(), buffer = gl.createBuffer();
      gl.bindVertexArray(vao);
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
      ATTRIBUTES.forEach((name, i) => {
        const at = gl.getAttribLocation(program, name);
        gl.enableVertexAttribArray(at);
        gl.vertexAttribPointer(at, 4, gl.FLOAT, false, STRIDE, i * 16);
        gl.vertexAttribDivisor(at, 1);
      });
      slots.push({ vao, buffer, count: 0 });
    }
    gl.bindVertexArray(null);
    gl.useProgram(program);
    gl.uniform3fv(uniform.u_palette, palette.flatMap((hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)));
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
    state = 'ready';
  }

  const set = (values) => {
    for (const [name, value] of Object.entries(values)) {
      if (Array.isArray(value)) gl.uniform2fv(uniform[name], value);
      else gl.uniform1f(uniform[name], value);
    }
  };

  return {
    // Checks without waiting where the browser can tell; otherwise waits for the build.
    get ready() {
      if (state === 'building' && (!parallel || gl.getProgramParameter(program, parallel.COMPLETION_STATUS_KHR))) finish();
      return state === 'ready';
    },
    get failed() {
      return state === 'failed';
    },
    // Takes a planned change into buffer `slot` (0 or 1): 20 floats per triangle, laid out as above.
    load(slot, data, n) {
      slots[slot].count = n;
      gl.bindBuffer(gl.ARRAY_BUFFER, slots[slot].buffer);
      gl.bufferData(gl.ARRAY_BUFFER, data, gl.DYNAMIC_DRAW);
    },
    // Draws the changes in `batches` ({ slot, ...their own uniforms }) with the `shared` uniforms.
    draw(view, shared, batches) {
      gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.useProgram(program);
      set(shared);
      for (const { slot, ...own } of batches) {
        if (!slots[slot].count) continue;
        set(own);
        gl.bindVertexArray(slots[slot].vao);
        gl.drawArraysInstanced(gl.TRIANGLES, 0, 3, slots[slot].count);
      }
      gl.bindVertexArray(null);
    },
  };
}

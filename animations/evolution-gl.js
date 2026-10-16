// GPU renderer for the evolution animation. Every triangle's whole journey from
// one stage to the next is worked out in the vertex shader, so tens of thousands
// of them cost the page almost nothing per frame.
//
// Each triangle is one instance with four vec4 attributes, written by the
// planner in evolution.js (see LAYOUT there):
//   from, to  x, y (units from the centre, or radius and angle for dust), height, dust flag
//   look      size from, size to, colour from, colour to (palette indices)
//   more      delay, seed, resting angle from, resting angle to

const VERTEX = `#version 300 es
precision highp float;

in vec4 a_from;
in vec4 a_to;
in vec4 a_look;
in vec4 a_more;

uniform float u_progress;  // 0 to 1 through a move, above 1 while a stage holds
uniform float u_previous;  // the same one frame earlier, to see which way triangles go
uniform float u_clock;     // seconds
uniform float u_step;      // seconds since the previous frame
uniform float u_spread;    // how far the change sweeps across the form
uniform float u_swirl;     // units of swirl in mid flight
uniform float u_breath;    // units of drift at rest
uniform float u_freq;      // swirl features per unit
uniform float u_twist;     // radians the whole form spirals about the centre in mid change
uniform float u_spin;      // radians per second the dust turns
uniform float u_yaw;       // radians the form turns about its vertical axis
uniform float u_depth;     // units a full height stands out of the page
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

float settle(float progress) {
  return clamp(progress * (1.0 + u_spread) - a_more.x, 0.0, 1.0);
}

// Where the triangle is (units from the centre, plus height) at a moment of the move.
vec3 at(float progress, float clock) {
  float u = settle(progress);
  float e = u * u * u * (u * (u * 6.0 - 15.0) + 10.0);
  vec2 p = mix(place(a_from, clock), place(a_to, clock), e);
  float h = mix(a_from.z, a_to.z, e);
  float flight = sin(3.14159265 * u);
  p += curl(p * u_freq, clock * 0.08) * (u_breath + u_swirl * flight);
  // the middle turns further than the rim, so the change spirals like a galaxy
  float a = u_twist * flight / (1.0 + dot(p, p) / 3600.0);
  p = mat2(cos(a), sin(a), -sin(a), cos(a)) * p;
  return vec3(p, h);
}

const float TAU = 6.28318530718;

void main() {
  float u = settle(u_progress);
  float e = u * u * u * (u * (u * 6.0 - 15.0) + 10.0);
  vec3 p = at(u_progress, u_clock);
  vec3 q = at(u_previous, u_clock - u_step);

  // Moving triangles point where they are going; resting ones turn to their stage's angle.
  vec2 v = (p.xy - q.xy) * u_scale;
  float rest = a_more.z + (mod(a_more.w - a_more.z + 3.14159265, TAU) - 3.14159265) * e;
  float heading = atan(v.y, v.x);
  float w = smoothstep(0.12, 0.7, length(v));
  float angle = rest + (mod(heading - rest + 3.14159265, TAU) - 3.14159265) * w;

  // A gentle turn in depth: heights shift against the flat outline, dust drifts in parallax.
  float dust = mix(a_from.w, a_to.w, e);
  float z = p.z * u_depth;
  float cy = cos(u_yaw), sy = sin(u_yaw);
  vec3 r = vec3(p.x * cy + z * sy, p.y, -p.x * sy + z * cy);
  float near = 600.0 / (600.0 - r.z);

  float size = mix(a_look.x, a_look.y, e) * near;
  float twinkle = 0.65 + 0.35 * sin(u_clock * (1.3 + a_more.y * 1.7) + a_more.y * TAU);
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

const ATTRIBUTES = ['a_from', 'a_to', 'a_look', 'a_more'];

function compile(gl, type, source) {
  const shader = gl.createShader(type);
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(shader));
  return shader;
}

// Returns a renderer for a WebGL2 context, or null if the shaders won't build.
export function createRenderer(gl, palette) {
  let program;
  try {
    program = gl.createProgram();
    gl.attachShader(program, compile(gl, gl.VERTEX_SHADER, VERTEX));
    gl.attachShader(program, compile(gl, gl.FRAGMENT_SHADER, FRAGMENT));
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program));
  } catch (error) {
    console.warn('Evolution animation: falling back to 2D drawing.', error);
    return null;
  }

  const uniform = {};
  for (let i = 0, n = gl.getProgramParameter(program, gl.ACTIVE_UNIFORMS); i < n; i++) {
    const name = gl.getActiveUniform(program, i).name.replace('[0]', '');
    uniform[name] = gl.getUniformLocation(program, name);
  }

  const vao = gl.createVertexArray();
  const buffer = gl.createBuffer();
  gl.bindVertexArray(vao);
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  ATTRIBUTES.forEach((name, i) => {
    const at = gl.getAttribLocation(program, name);
    gl.enableVertexAttribArray(at);
    gl.vertexAttribPointer(at, 4, gl.FLOAT, false, 64, i * 16);
    gl.vertexAttribDivisor(at, 1);
  });
  gl.bindVertexArray(null);

  gl.useProgram(program);
  gl.uniform3fv(uniform.u_palette, palette.flatMap((hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)));
  gl.enable(gl.BLEND);
  gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);

  let count = 0;

  return {
    // Takes the next move: 16 floats per triangle, laid out as described above.
    load(data, n) {
      count = n;
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
      gl.bufferData(gl.ARRAY_BUFFER, data, gl.DYNAMIC_DRAW);
    },
    draw(view, values) {
      gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      if (!count) return;
      gl.useProgram(program);
      for (const [name, value] of Object.entries(values)) {
        if (Array.isArray(value)) gl.uniform2fv(uniform[name], value);
        else gl.uniform1f(uniform[name], value);
      }
      gl.bindVertexArray(vao);
      gl.drawArraysInstanced(gl.TRIANGLES, 0, 3, count);
      gl.bindVertexArray(null);
    },
  };
}

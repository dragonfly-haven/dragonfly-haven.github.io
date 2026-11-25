// GPU renderer for the coelacanth. Every dash is a quad laid along its stroke,
// with its edges smoothed in the fragment shader as a canvas smooths them, and
// every fin is posed in the vertex shader from a handful of matrices, so the
// tens of thousands of dashes cost the page almost nothing per frame. The rise
// is worked out there too: each grain's flight from the fossil to its place.
//
// The layers go down as the 2D drawing in coelacanth.js lays them: the fins on
// the far side; then the body, clearing what it hides of them (or, while it
// rises, its grains); then the other fins, each clearing the body behind it.
//
// A dash is one instance of 12 floats, written by coelacanth.js:
//   p0, p1    its ends: for a lobed fin s, c, n along, across and out of the fin, and
//             the level of its bend; for a fan fin x, y in the middle plane, the
//             share f of the way out to the rim, unused
//   q         the outward normal of a lobe's dash (zero for none), which hides it
//             when it faces away; then its width in CSS px, negative for square ends
// A grain of the rise is one instance of 12 floats:
//   g0        where it lies in the fossil x, y, its angle there, half its length
//             (negative for a thin dash)
//   g1        the control point of its arc x, y; when it lifts and how long it flies
//             (flight -1 for loose sand, with g1.x when it drifts off)
//   g2        where it lands: its two ends

const COMMON = `#version 300 es
precision highp float;
uniform int u_mode;        // 0: a lobed fin, 1: a fan fin
uniform mat3 u_M[17];      // a lobed fin's frame at each level of its bend, transposed
uniform vec3 u_T;          // and its root, in camera space
uniform mat3 u_G;          // model to camera space, transposed
uniform vec4 u_sway;       // a fan fin's wave: amplitude, phase now, wave number, amount
uniform float u_reach;     // how far a fin has unfurled: its last level, or share of the way out
uniform vec4 u_proj;       // the picture's origin x, y, CSS px per unit, camera distance
uniform vec2 u_view;       // CSS px
uniform float u_ratio;     // device px per CSS px

vec3 posed(vec4 p) {
  if (u_mode == 0) return u_T + p.xyz * u_M[int(p.w + 0.5)];
  float z = u_sway.w * u_sway.x * pow(p.z, 1.5) * sin(u_sway.y - u_sway.z * (p.x + 50.0));
  return vec3(p.xy, z) * u_G;
}

vec2 screen(vec3 q) {
  float k = u_proj.w / (u_proj.w - q.z) * u_proj.z;
  return vec2(u_proj.x + q.x * k, u_proj.y - q.y * k);
}

vec4 clip(vec2 px) {
  return vec4(px.x / u_view.x * 2.0 - 1.0, 1.0 - px.y / u_view.y * 2.0, 0.0, 1.0);
}

// A quad round the dash from a to b (device px), a pixel wider all round for its soft edges.
out vec2 v_local;
out vec2 v_half;
vec4 dash(vec2 a, vec2 b, float hw, bool square) {
  vec2 d = b - a;
  float len = length(d);
  vec2 dir = len > 1e-4 ? d / len : vec2(1.0, 0.0);
  float hl = len * 0.5 + (square ? hw : 0.0);
  int k = gl_VertexID;
  vec2 corner = vec2(k == 1 || k == 2 || k == 4 ? 1.0 : -1.0, k == 2 || k == 4 || k == 5 ? 1.0 : -1.0);
  v_local = corner * vec2(hl + 1.0, hw + 1.0);
  v_half = vec2(hl, hw);
  return clip(((a + b) * 0.5 + dir * v_local.x + vec2(-dir.y, dir.x) * v_local.y) / u_ratio);
}
const vec4 HIDDEN = vec4(2.0, 2.0, 2.0, 1.0); // outside the view, so nothing is drawn
`;

const SEGMENT = `${COMMON}
in vec4 a_p0;
in vec4 a_p1;
in vec4 a_q;
void main() {
  bool hidden = (u_mode == 0 ? a_p0.w : a_p0.z) > u_reach;
  if (u_mode == 0 && dot(a_q.xyz, a_q.xyz) > 0.0) hidden = hidden || (a_q.xyz * u_M[int(a_p0.w + 0.5)]).z < 0.02;
  if (hidden) {
    gl_Position = HIDDEN;
    v_local = v_half = vec2(0.0);
    return;
  }
  vec2 a = screen(posed(a_p0)) * u_ratio, b = screen(posed(a_p1)) * u_ratio;
  gl_Position = dash(a, b, abs(a_q.w) * 0.5 * u_ratio, a_q.w < 0.0);
}`;

const RISE = `${COMMON}
in vec4 a_g0;
in vec4 a_g1;
in vec4 a_g2;
uniform float u_time;      // seconds into the rise
uniform float u_appear;    // how far the fossil has faded in
uniform float u_width;     // a dash's width, CSS px
uniform float u_sand;      // how dark a grain lying still is
flat out float v_group;
const float TAU = 6.28318530718;
float smoother(float t) { return t * t * t * (t * (t * 6.0 - 15.0) + 10.0); }
void main() {
  vec2 p;
  float angle, half_, tone;
  bool thin = a_g0.w < 0.0;
  if (a_g1.w < 0.0) {
    // Loose sand, drifting off once the fish has risen.
    float gone = smoother(clamp((u_time - a_g1.x) / 1.2, 0.0, 1.0));
    half_ = a_g0.w;
    p = a_g0.xy + gone * half_ * vec2(3.0, 2.0);
    angle = a_g0.z;
    tone = u_sand * u_appear * (1.0 - gone);
  } else {
    float u = clamp((u_time - a_g1.z) / a_g1.w, 0.0, 1.0), e = smoother(u), f = 1.0 - e;
    vec2 home = (a_g2.xy + a_g2.zw) * 0.5;
    p = f * f * a_g0.xy + 2.0 * f * e * a_g1.xy + e * e * home;
    vec2 d = a_g2.zw - a_g2.xy;
    float end = atan(d.y, d.x), start = a_g0.z, turn = end - start;
    angle = start + (turn - TAU * floor(turn / TAU + 0.5)) * e;
    half_ = abs(a_g0.w);
    tone = u > 0.0 ? u_sand + (1.0 - u_sand) * e : u_sand * u_appear;
  }
  // In the six tones the 2D drawing uses; each tone's grains merge as one stroke.
  v_group = floor(tone * 6.0 + 0.5);
  if (v_group < 1.0) {
    gl_Position = HIDDEN;
    v_local = v_half = vec2(0.0);
    return;
  }
  vec2 dir = vec2(cos(angle), sin(angle)) * half_;
  gl_Position = dash((p - dir) * u_ratio, (p + dir) * u_ratio, u_width * (thin ? 0.35 : 0.5) * u_ratio, false);
}`;

const FILL = `${COMMON}
in vec4 a_p;
void main() {
  v_local = v_half = vec2(0.0);
  gl_Position = clip(screen(posed(a_p)));
}`;

const QUAD = `#version 300 es
precision highp float;
out vec2 v_uv;
void main() {
  int k = gl_VertexID;
  vec2 corner = vec2(k == 1 || k == 2 || k == 4 ? 1.0 : 0.0, k == 2 || k == 4 || k == 5 ? 1.0 : 0.0);
  v_uv = vec2(corner.x, 1.0 - corner.y);
  gl_Position = vec4(corner * 2.0 - 1.0, 0.0, 1.0);
}`;

// A dash's coverage of each pixel: the overlap of the pixel's square with it,
// along and across, as a canvas antialiases a stroke.
const INKED = `#version 300 es
precision highp float;
in vec2 v_local;
in vec2 v_half;
uniform vec3 u_ink;
uniform float u_alpha;
out vec4 colour;
float overlap(float x, float h) { return clamp(min(x + 0.5, h) - max(x - 0.5, -h), 0.0, 1.0); }
void main() {
  float a = overlap(v_local.x, v_half.x) * overlap(v_local.y, v_half.y) * u_alpha;
  colour = vec4(u_ink * a, a);
}`;

// The rise: each grain's coverage, added up in the channel of its tone, for
// MERGED to lay down tone by tone.
const GROUPED = `#version 300 es
precision highp float;
in vec2 v_local;
in vec2 v_half;
flat in float v_group;
layout(location = 0) out vec4 tones1to4;
layout(location = 1) out vec4 tones5to6;
float overlap(float x, float h) { return clamp(min(x + 0.5, h) - max(x - 0.5, -h), 0.0, 1.0); }
void main() {
  float a = overlap(v_local.x, v_half.x) * overlap(v_local.y, v_half.y);
  tones1to4 = a * vec4(equal(vec4(v_group), vec4(1.0, 2.0, 3.0, 4.0)));
  tones5to6 = a * vec4(equal(vec4(v_group), vec4(5.0, 6.0, 7.0, 8.0)));
}`;

// Lays the six tones down palest first, each over the last, as the 2D drawing strokes them.
const MERGED = `#version 300 es
precision highp float;
in vec2 v_uv;
uniform sampler2D u_tones1to4;
uniform sampler2D u_tones5to6;
uniform vec3 u_ink;
out vec4 colour;
void main() {
  vec4 lo = texture(u_tones1to4, v_uv), hi = texture(u_tones5to6, v_uv);
  float tones[6] = float[6](lo.r, lo.g, lo.b, lo.a, hi.r, hi.g);
  float a = 0.0;
  for (int k = 0; k < 6; k++) {
    float c = tones[k] * float(k + 1) / 6.0;
    a = c + a * (1.0 - c);
  }
  colour = vec4(u_ink * a, a);
}`;

const FLAT = `#version 300 es
precision highp float;
in vec2 v_local;
in vec2 v_half;
uniform vec3 u_ink;
uniform float u_alpha;
out vec4 colour;
void main() { colour = vec4(u_ink * u_alpha, u_alpha); }`;

const TEXTURED = `#version 300 es
precision highp float;
in vec2 v_uv;
uniform sampler2D u_image;
out vec4 colour;
void main() { colour = texture(u_image, v_uv); }`;

// Returns a renderer for the canvas, or null where WebGL2 isn't to be had, runs
// only in software (slower than drawing in 2D) or its shaders won't build, in
// which case the caller draws in 2D.
export function createRenderer(canvas, ink) {
  const gl = canvas.getContext('webgl2', { alpha: true, premultipliedAlpha: true, antialias: false, depth: false, stencil: false, failIfMajorPerformanceCaveat: true });
  if (!gl) return null;
  const info = gl.getExtension('WEBGL_debug_renderer_info');
  if (/swiftshader|llvmpipe|softpipe|software|basic render/i.test(gl.getParameter(info ? info.UNMASKED_RENDERER_WEBGL : gl.RENDERER))) return null;
  const build = (vs, fs, attributes) => {
    const program = gl.createProgram();
    const shaders = [[gl.VERTEX_SHADER, vs], [gl.FRAGMENT_SHADER, fs]].map(([type, source]) => {
      const shader = gl.createShader(type);
      gl.shaderSource(shader, source);
      gl.compileShader(shader);
      gl.attachShader(program, shader);
      return shader;
    });
    attributes.forEach((name, i) => gl.bindAttribLocation(program, i, name));
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      const log = [gl.getProgramInfoLog(program), ...shaders.map((sh) => gl.getShaderInfoLog(sh))].filter(Boolean).join('\n');
      throw new Error(log);
    }
    const uniform = {};
    for (let i = 0, n = gl.getProgramParameter(program, gl.ACTIVE_UNIFORMS); i < n; i++) {
      const name = gl.getActiveUniform(program, i).name.replace('[0]', '');
      uniform[name] = gl.getUniformLocation(program, name);
    }
    return { program, uniform };
  };
  let programs;
  try {
    programs = {
      segment: build(SEGMENT, INKED, ['a_p0', 'a_p1', 'a_q']),
      rise: build(RISE, GROUPED, ['a_g0', 'a_g1', 'a_g2']),
      merged: build(QUAD.replace('1.0 - corner.y', 'corner.y'), MERGED, []), // a framebuffer's rows run from the bottom
      fill: build(FILL, FLAT, ['a_p']),
      quad: build(QUAD, TEXTURED, []),
    };
  } catch (error) {
    console.warn('Coelacanth: falling back to 2D drawing.', error.message);
    return null;
  }
  const inkRGB = [1, 3, 5].map((i) => parseInt(ink.slice(i, i + 2), 16) / 255);
  for (const { program, uniform } of [programs.segment, programs.fill, programs.merged]) {
    gl.useProgram(program);
    if (uniform.u_ink) gl.uniform3fv(uniform.u_ink, inkRGB);
    if (uniform.u_alpha) gl.uniform1f(uniform.u_alpha, 1);
  }
  gl.useProgram(programs.merged.program);
  gl.uniform1i(programs.merged.uniform.u_tones1to4, 0);
  gl.uniform1i(programs.merged.uniform.u_tones5to6, 1);
  gl.enable(gl.BLEND);

  // Instances of three vec4s, as described above.
  const instances = (data) => {
    const vao = gl.createVertexArray(), buffer = gl.createBuffer();
    gl.bindVertexArray(vao);
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
    for (let i = 0; i < 3; i++) {
      gl.enableVertexAttribArray(i);
      gl.vertexAttribPointer(i, 4, gl.FLOAT, false, 48, i * 16);
      gl.vertexAttribDivisor(i, 1);
    }
    gl.bindVertexArray(null);
    return { vao, buffer, count: data.length / 12 };
  };
  const vertices = (data) => {
    const vao = gl.createVertexArray(), buffer = gl.createBuffer();
    gl.bindVertexArray(vao);
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 4, gl.FLOAT, false, 16, 0);
    gl.bindVertexArray(null);
    return { vao, buffer, count: data.length / 4 };
  };
  const texture = (image) => {
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, true);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image);
    for (const [key, value] of [[gl.TEXTURE_MIN_FILTER, gl.NEAREST], [gl.TEXTURE_MAG_FILTER, gl.NEAREST], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D, key, value);
    return tex;
  };
  const emptyVao = gl.createVertexArray();

  // Two textures the size of the canvas that the rise adds its tones up in.
  const tones = { framebuffer: gl.createFramebuffer(), textures: [], width: 0, height: 0 };
  const sizeTones = () => {
    const w = gl.drawingBufferWidth, h = gl.drawingBufferHeight;
    if (tones.width === w && tones.height === h) return;
    tones.textures.forEach((tex) => gl.deleteTexture(tex));
    gl.bindFramebuffer(gl.FRAMEBUFFER, tones.framebuffer);
    tones.textures = [0, 1].map((k) => {
      const tex = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.texStorage2D(gl.TEXTURE_2D, 1, gl.RGBA8, w, h);
      for (const [key, value] of [[gl.TEXTURE_MIN_FILTER, gl.NEAREST], [gl.TEXTURE_MAG_FILTER, gl.NEAREST], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D, key, value);
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0 + k, gl.TEXTURE_2D, tex, 0);
      return tex;
    });
    gl.drawBuffers([gl.COLOR_ATTACHMENT0, gl.COLOR_ATTACHMENT1]);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    Object.assign(tones, { width: w, height: h });
  };

  let scene = null;
  const free = () => {
    if (!scene) return;
    const all = [scene.rise, ...scene.fins.flatMap((f) => [f.dashes, f.clear?.segs, f.clear?.fill])].filter(Boolean);
    for (const { vao, buffer } of all) {
      gl.deleteVertexArray(vao);
      gl.deleteBuffer(buffer);
    }
    gl.deleteTexture(scene.body);
    gl.deleteTexture(scene.mask);
    scene = null;
  };

  const OVER = () => gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
  const CLEAR = () => gl.blendFunc(gl.ZERO, gl.ONE_MINUS_SRC_ALPHA);

  // The view and projection, set on each program that uses them.
  const shared = (uniform) => {
    gl.uniform4fv(uniform.u_proj, scene.proj);
    gl.uniform2f(uniform.u_view, scene.width, scene.height);
    gl.uniform1f(uniform.u_ratio, scene.ratio);
  };
  const posing = (uniform, fin, pose) => {
    gl.uniform1i(uniform.u_mode, fin.mode);
    gl.uniform1f(uniform.u_reach, pose.reach);
    if (fin.mode === 0) {
      gl.uniformMatrix3fv(uniform.u_M, false, pose.M);
      gl.uniform3fv(uniform.u_T, pose.T);
    } else {
      gl.uniformMatrix3fv(uniform.u_G, false, scene.G);
      gl.uniform4fv(uniform.u_sway, pose.sway);
    }
  };
  const drawFin = (pose) => {
    const fin = scene.fins[pose.index];
    if (pose.grow <= 0) return;
    const { segment, fill } = programs;
    if (fin.clear) {
      CLEAR();
      gl.useProgram(fill.program);
      shared(fill.uniform);
      posing(fill.uniform, fin, pose);
      gl.uniform1f(fill.uniform.u_alpha, pose.grow);
      gl.bindVertexArray(fin.clear.fill.vao);
      gl.drawArrays(gl.TRIANGLES, 0, fin.clear.fill.count);
    }
    gl.useProgram(segment.program);
    shared(segment.uniform);
    posing(segment.uniform, fin, pose);
    if (fin.clear) {
      gl.uniform1f(segment.uniform.u_alpha, pose.grow);
      gl.bindVertexArray(fin.clear.segs.vao);
      gl.drawArraysInstanced(gl.TRIANGLES, 0, 6, fin.clear.segs.count);
      gl.uniform1f(segment.uniform.u_alpha, 1);
    }
    OVER();
    gl.bindVertexArray(fin.dashes.vao);
    gl.drawArraysInstanced(gl.TRIANGLES, 0, 6, fin.dashes.count);
  };
  const image = (tex) => {
    gl.useProgram(programs.quad.program);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.bindVertexArray(emptyVao);
    gl.drawArrays(gl.TRIANGLES, 0, 6);
  };

  return {
    gl,
    // Takes a laid-out fish: see coelacanth.js for what each part holds.
    load(next) {
      free();
      scene = {
        width: next.width, height: next.height, ratio: next.ratio, proj: next.proj, G: next.G,
        body: texture(next.body), mask: texture(next.mask),
        rise: instances(next.grains),
        fins: next.fins.map((f) => ({
          mode: f.mode,
          dashes: instances(f.dashes),
          clear: f.clear && { segs: instances(f.clear.segs), fill: vertices(f.clear.fill) },
        })),
      };
    },
    // Draws a frame: `back` and `front` are the fins' poses behind and in front
    // of the body; `rise`, while it rises, its time and look.
    draw({ back, front, rise }) {
      if (!scene || gl.isContextLost()) return;
      gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      back.forEach(drawFin);
      if (rise) {
        // The grains of each tone add up, side by side as one stroke's dashes do
        // in a canvas; then the tones go down over the fins behind.
        sizeTones();
        gl.bindFramebuffer(gl.FRAMEBUFFER, tones.framebuffer);
        gl.clear(gl.COLOR_BUFFER_BIT);
        gl.blendFunc(gl.ONE, gl.ONE);
        const { program, uniform } = programs.rise;
        gl.useProgram(program);
        shared(uniform);
        gl.uniform1f(uniform.u_time, rise.time);
        gl.uniform1f(uniform.u_appear, rise.appear);
        gl.uniform1f(uniform.u_width, rise.width);
        gl.uniform1f(uniform.u_sand, rise.sand);
        gl.bindVertexArray(scene.rise.vao);
        gl.drawArraysInstanced(gl.TRIANGLES, 0, 6, scene.rise.count);
        gl.bindFramebuffer(gl.FRAMEBUFFER, null);
        OVER();
        gl.useProgram(programs.merged.program);
        tones.textures.forEach((tex, k) => {
          gl.activeTexture(gl.TEXTURE0 + k);
          gl.bindTexture(gl.TEXTURE_2D, tex);
        });
        gl.activeTexture(gl.TEXTURE0);
        gl.bindVertexArray(emptyVao);
        gl.drawArrays(gl.TRIANGLES, 0, 6);
      } else {
        CLEAR();
        image(scene.mask);
        OVER();
        image(scene.body);
      }
      front.forEach(drawFin);
      gl.bindVertexArray(null);
    },
    destroy() {
      free();
      tones.textures.forEach((tex) => gl.deleteTexture(tex));
      gl.deleteFramebuffer(tones.framebuffer);
      gl.getExtension('WEBGL_lose_context')?.loseContext();
    },
  };
}

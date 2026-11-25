// Mounts the animations into the page's #evolution and #dragonfly spots:
//   <script type="module" src="animations/site.js"></script>
//
// The address can pick other styles, e.g. /?evolution=triangles&dragonfly=shatter:
// the evolution plays the pen drawings (sketch.js) unless it asks for the
// golden triangles (evolution.js).

import { mountDragonfly } from './dragonfly.js';

const params = new URLSearchParams(location.search);

const evolution = document.getElementById('evolution');
if (evolution) {
  const style = params.get('evolution') === 'triangles' ? './evolution.js' : './sketch.js';
  import(style).then(({ mountEvolution }) => mountEvolution(evolution));
}

const dragonfly = document.getElementById('dragonfly');
if (dragonfly) mountDragonfly(dragonfly, { style: params.get('dragonfly') || 'crystallise' });

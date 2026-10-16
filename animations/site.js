// Mounts the chosen animations into the page's #evolution and #dragonfly spots:
//   <script type="module" src="animations/site.js"></script>
// Other styles can be tried on the live page with ?evolution=murmur&dragonfly=shatter.

import { mountEvolution } from './evolution.js';
import { mountDragonfly } from './dragonfly.js';

const params = new URLSearchParams(location.search);

const evolution = document.getElementById('evolution');
if (evolution) mountEvolution(evolution, { style: params.get('evolution') || 'flow' });

const dragonfly = document.getElementById('dragonfly');
if (dragonfly) mountDragonfly(dragonfly, { style: params.get('dragonfly') || 'crystallise' });

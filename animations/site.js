// Mounts the chosen animations into the page's #evolution and #dragonfly spots:
//   <script type="module" src="animations/site.js"></script>

import { mountEvolution } from './evolution.js';
import { mountDragonfly } from './dragonfly.js';

const evolution = document.getElementById('evolution');
if (evolution) mountEvolution(evolution, { style: 'flow' });

const dragonfly = document.getElementById('dragonfly');
if (dragonfly) mountDragonfly(dragonfly, { style: 'crystallise' });

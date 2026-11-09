// Mounts the animations into the page's #evolution, #dragonfly and #coelacanth spots:
//   <script type="module" src="animations/site.js"></script>

import { mountEvolution } from './evolution.js';
import { mountDragonfly } from './dragonfly.js';
import { mountCoelacanth } from './coelacanth.js';

const params = new URLSearchParams(location.search);

const evolution = document.getElementById('evolution');
if (evolution) mountEvolution(evolution);

const dragonfly = document.getElementById('dragonfly');
if (dragonfly) mountDragonfly(dragonfly, { style: params.get('dragonfly') || 'crystallise' });

const coelacanth = document.getElementById('coelacanth');
if (coelacanth) mountCoelacanth(coelacanth, { rise: true });

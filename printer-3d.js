const host = document.querySelector('#printer-3d');
const status = document.querySelector('#printer-3d-status');
try {
  const [THREE, { OrbitControls }, { STLLoader }] = await Promise.all([
    import('three'), import('three/addons/controls/OrbitControls.js'), import('three/addons/loaders/STLLoader.js')
  ]);
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(38, 1, 0.01, 100);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = false;
  controls.minDistance = 1.3; controls.maxDistance = 7;
  status.textContent = 'Loading the 3D printer model…';
  const modelURL = new URL('./models/ender-3/ender-3.stl', import.meta.url);
  const response = await fetch(modelURL, { signal: AbortSignal.timeout(30000) });
  if (!response.ok) throw new Error(`Model download failed (HTTP ${response.status}).`);
  const geometry = new STLLoader().parse(await response.arrayBuffer());
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  const size = geometry.boundingBox.getSize(new THREE.Vector3());
  const center = geometry.boundingBox.getCenter(new THREE.Vector3());
  const scale = 2 / Math.max(size.x, size.y, size.z);
  geometry.center(); geometry.scale(scale, scale, scale);
  const mesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ color: 0x536570, metalness: 0.3, roughness: 0.65 }));
  scene.add(mesh, new THREE.HemisphereLight(0xffffff, 0x65717b, 3));
  const light = new THREE.DirectionalLight(0xffe5cf, 4); light.position.set(3, 4, 5); scene.add(light);
  // Anchors in the original CAD coordinate system, transformed with the mesh.
  const anchors = [
    ['Extruder repair', [76, 224, -40]],
    ['Stepper motor and gear', [76, 196, -40]],
    ['Calibration and first prints', [-43, 100, -80]],
    ['Hotend repair', [-88, 137, -144]]
  ];
  const overlay = document.createElement('div');
  overlay.className = 'printer-hotspots';
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('aria-hidden', 'true'); overlay.append(svg);
  const hotspots = anchors.map(([label, coordinates], index) => {
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'printer-hotspot';
    button.dataset.part = index; button.textContent = index + 1;
    button.setAttribute('aria-label', `${index + 1}: ${label}`);
    button.setAttribute('aria-controls', 'printer-detail');
    button.setAttribute('aria-pressed', document.querySelector(`.printer-part-list [data-part="${index}"]`).getAttribute('aria-pressed'));
    button.title = label;
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line'); svg.append(line);
    overlay.append(button);
    return {button, line, point: new THREE.Vector3(...coordinates).sub(center).multiplyScalar(scale)};
  });
  function positionHotspots() {
    const width = host.clientWidth, height = host.clientHeight;
    const placed = [];
    for (const {button, line, point} of hotspots) {
      const projected = point.clone().project(camera);
      const visible = projected.z > -1 && projected.z < 1 && Math.abs(projected.x) < 1 && Math.abs(projected.y) < 1;
      button.hidden = !visible; line.style.display = visible ? '' : 'none';
      if (!visible) continue;
      const x = (projected.x + 1) * width / 2, y = (1 - projected.y) * height / 2;
      const bx = Math.max(26, Math.min(width - 26, x));
      let by = Math.max(26, Math.min(height - 26, y));
      for (let attempt = 0; attempt < 12 && placed.some(p => Math.hypot(p.x - bx, p.y - by) < 50); attempt++) {
        by = Math.max(26, Math.min(height - 26, y + (attempt % 2 ? -1 : 1) * Math.ceil((attempt + 1) / 2) * 50));
      }
      placed.push({x: bx, y: by});
      button.style.left = `${bx}px`; button.style.top = `${by}px`;
      for (const [key,value] of Object.entries({x1:x,y1:y,x2:bx,y2:by})) line.setAttribute(key,value);
    }
  }
  function render() { renderer.render(scene, camera); positionHotspots(); }
  function reset() { camera.position.set(2.7, 1.8, 3); controls.target.set(0, 0, 0); controls.update(); render(); }
  host.append(renderer.domElement, overlay); host.hidden = false;
  renderer.domElement.setAttribute('aria-label', 'Interactive Ender 3 model. Drag to rotate, right-drag to pan, scroll to zoom. Use the buttons below for keyboard controls.');
  controls.addEventListener('change', render);
  new ResizeObserver(() => { const {width,height} = host.getBoundingClientRect(); renderer.setSize(width,height); camera.aspect=width/height; camera.updateProjectionMatrix(); render(); }).observe(host);
  document.querySelectorAll('[data-view]').forEach(button => {
    button.disabled = false;
    button.addEventListener('click', () => {
      const action = button.dataset.view;
      if(action === 'reset') return reset();
      const offset = camera.position.clone().sub(controls.target);
      if(action === 'left' || action === 'right') offset.applyAxisAngle(new THREE.Vector3(0,1,0), action === 'left' ? -0.25 : 0.25);
      else offset.multiplyScalar(action === 'in' ? 0.85 : 1.15).clampLength(1.3,7);
      camera.position.copy(controls.target).add(offset); controls.update(); render();
    });
  });
  reset();
  document.querySelector('.printer-map').hidden = true;
  status.textContent = 'Click a numbered point to see the repair story. Drag to orbit · Right-drag to pan · Scroll to zoom · On touch, use two fingers to pan or pinch.';
  renderer.domElement.addEventListener('webglcontextlost', event => { event.preventDefault(); host.hidden=true; document.querySelector('.printer-map').hidden=false; status.textContent='3D view unavailable. Explore the printer photo below.'; });
} catch (error) {
  host.hidden = true;
  status.textContent = location.protocol === 'file:'
    ? 'Open this page through a local web server to load the 3D model. Browsers block model downloads from file:// pages.'
    : `3D view unavailable: ${error.message} Explore the printer photo below, or reload to try again.`;
  console.warn('Printer viewer unavailable:', error);
}

// assets/js/viewer3d.js
// Interactive Three.js "as-built" viewer for the YOU WELLNESS CLINIC portal.
// Works with any element: <div class="asbuilt-3d-widget" data-gltf-src="assets/models/x.gltf">
// Falls back to a procedural low-poly clinic tower when no GLTF is present/loadable.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

class AsBuiltModelViewer {
  constructor() {
    this.activeInstances = new Map();
    this.ready = false;
  }

  initViewers(targetContainer = document) {
    if (!targetContainer) return;
    this.destroyAll();
    const widgets = targetContainer.querySelectorAll('.asbuilt-3d-widget');
    widgets.forEach((widget, index) => {
      const wid = 'asbuilt-viewer-' + index + '-' + Date.now();
      widget.setAttribute('id', wid);
      this.activeInstances.set(wid, this.createSceneInstance(widget, widget.getAttribute('data-gltf-src')));
    });
    this.ready = true;
  }

  createSceneInstance(container, modelUrl) {
    const width = container.clientWidth || 640;
    const height = container.clientHeight || 480;
    const statusText = container.querySelector('.status-text');

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x050811, 0.02);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(7, 6, 9);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.shadowMap.enabled = true;
    renderer.domElement.style.width = '100%';
    renderer.domElement.style.height = '100%';
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.maxPolarAngle = Math.PI / 2 + 0.05;

    scene.add(new THREE.AmbientLight(0xffffff, 0.75));
    const dir = new THREE.DirectionalLight(0x00f2fe, 2.2);
    dir.position.set(12, 18, 10);
    scene.add(dir);
    const pt = new THREE.PointLight(0x4facfe, 3.2, 26);
    pt.position.set(-6, 7, -6);
    scene.add(pt);

    const grid = new THREE.GridHelper(22, 22, 0x00f2fe, 0x152238);
    grid.position.y = -0.01;
    scene.add(grid);

    let loadedModel = null;
    let isWireframe = false;
    const animate = () => {
      this._raf = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    const resizeObserver = new ResizeObserver(() => {
      const w = container.clientWidth, h = container.clientHeight;
      if (!w || !h) return;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    });
    resizeObserver.observe(container);

    const loader = new GLTFLoader();
    if (modelUrl && /\.(gltf|glb)$/i.test(modelUrl)) {
      if (statusText) statusText.textContent = 'LOADING GLTF...';
      loader.load(
        modelUrl,
        (gltf) => {
          loadedModel = gltf.scene;
          scene.add(loadedModel);
          this.centerAndScaleModel(loadedModel, camera, controls);
          if (statusText) statusText.textContent = 'ONLINE (AS-BUILT)';
        },
        (xhr) => {
          if (statusText && xhr.total > 0) {
            statusText.textContent = 'LOADING ' + Math.round((xhr.loaded / xhr.total) * 100) + '%';
          }
        },
        () => {
          try { loadedModel = this.createFallbackTower(); scene.add(loadedModel); }
          catch (e) { console.warn('3D fallback failed', e); }
          if (statusText) statusText.textContent = 'DEMO MODEL (MOCKUP)';
        }
      );
    } else {
      try { loadedModel = this.createFallbackTower(); scene.add(loadedModel); }
      catch (e) { console.warn('3D fallback failed', e); }
      if (statusText) statusText.textContent = 'DEMO MODEL (MOCKUP)';
    }

    return {
      scene, camera, renderer, controls, loadedModel, isWireframe,
      resizeObserver, defaultCamPos: camera.position.clone()
    };
  }

  createFallbackTower() {
    const g = new THREE.Group();
    const dark = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.25, metalness: 0.85 });
    const cyan = new THREE.MeshBasicMaterial({ color: 0x00f2fe });
    const blueMat = new THREE.MeshStandardMaterial({ color: 0x2b6cb0, roughness: 0.3, metalness: 0.6, transparent: true, opacity: 0.55 });

    // podium
    const pod = new THREE.Mesh(new THREE.BoxGeometry(4.2, 0.6, 4.2), dark);
    pod.position.y = 0.3; g.add(pod);
    const podEdge = new THREE.LineSegments(
      new THREE.EdgesGeometry(pod.geometry), new THREE.LineBasicMaterial({ color: 0x00f2fe }));
    podEdge.position.y = 0.3; g.add(podEdge);

    // tower shaft
    const shaft = new THREE.Mesh(new THREE.BoxGeometry(2.4, 2.6, 2.4), dark);
    shaft.position.y = 1.9; g.add(shaft);
    const shaftEdge = new THREE.LineSegments(
      new THREE.EdgesGeometry(shaft.geometry), new THREE.LineBasicMaterial({ color: 0x00f2fe }));
    shaftEdge.position.y = 1.9; g.add(shaftEdge);

    // glass floors
    for (let i = 0; i < 3; i++) {
      const floor = new THREE.Mesh(new THREE.BoxGeometry(2.7, 0.05, 2.7), blueMat);
      floor.position.y = 1.0 + i * 0.7; g.add(floor);
    }

    // crown ring
    const ring = new THREE.Mesh(new THREE.TorusGeometry(1.55, 0.06, 8, 40), cyan);
    ring.position.y = 3.35; ring.rotation.x = Math.PI / 2; g.add(ring);

    // accent beams (LED columns)
    const beamGeo = new THREE.BoxGeometry(0.06, 2.6, 0.06);
    for (const [bx, bz] of [[-1.2, -1.2], [1.2, -1.2], [-1.2, 1.2], [1.2, 1.2]]) {
      const beam = new THREE.Mesh(beamGeo, cyan);
      beam.position.set(bx, 1.9, bz); g.add(beam);
    }
    return g;
  }

  centerAndScaleModel(model, camera, controls) {
    const box = new THREE.Box3().setFromObject(model);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z) || 1;
    const fov = camera.fov * (Math.PI / 180);
    const cz = Math.abs(maxDim / 2 / Math.tan(fov / 2)) * 2.2;
    model.position.x -= center.x;
    model.position.z -= center.z;
    model.position.y -= box.min.y;
    camera.position.set(cz * 0.7, cz * 0.6, cz);
    camera.lookAt(0, size.y / 2, 0);
    controls.target.set(0, size.y / 2, 0);
    controls.update();
  }

  toggleWireframe(button) {
    const widget = button.closest('.asbuilt-3d-widget');
    const inst = this.activeInstances.get(widget && widget.id);
    if (!inst || !inst.loadedModel) return;
    inst.isWireframe = !inst.isWireframe;
    button.classList.toggle('active', inst.isWireframe);
    inst.loadedModel.traverse((child) => {
      if (child.isMesh && child.material) child.material.wireframe = inst.isWireframe;
    });
  }

  toggleAutoRotate(button) {
    const widget = button.closest('.asbuilt-3d-widget');
    const inst = this.activeInstances.get(widget && widget.id);
    if (!inst) return;
    inst.controls.autoRotate = !inst.controls.autoRotate;
    inst.controls.autoRotateSpeed = 2.5;
    button.classList.toggle('active', inst.controls.autoRotate);
  }

  resetCamera() {
    this.activeInstances.forEach((inst) => {
      inst.controls.reset();
      inst.camera.position.copy(inst.defaultCamPos);
    });
  }

  destroyAll() {
    this.activeInstances.forEach((inst) => {
      cancelAnimationFrame(this._raf);
      inst.resizeObserver.disconnect();
      inst.renderer.dispose();
      if (inst.renderer.domElement.parentNode) {
        inst.renderer.domElement.parentNode.removeChild(inst.renderer.domElement);
      }
    });
    this.activeInstances.clear();
  }
}

export const asBuiltManager = new AsBuiltModelViewer();
window.asBuiltManager = asBuiltManager;

// init the currently visible chapter after module load (handles the first render)
window.addEventListener('DOMContentLoaded', () => {
  try {
    const active = document.getElementById('ch' + (window.state ? window.state.ch : 1));
    if (active) asBuiltManager.initViewers(active);
  } catch (e) { console.warn('3D first-init skipped:', e); }
});
import * as THREE from 'three';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';

const OBJECT_COLORS = {
  INSTRUMENT: 0x0f6e56,
  EQUIPMENT: 0x1c2430,
  VALVE: 0xb45309,
  TANK: 0x1d4ed8,
  PUMP: 0x0f766e,
  FLANGE: 0x9f1239,
  DEFAULT: 0x8b949e,
};

const LINE_COLORS = {
  BORDER: 0xb42318,
  DIMENSION: 0x1d4ed8,
  LIKELY_PIPE: 0x0f6e56,
};

const TEXT_CLASS = {
  INSTRUMENT_TAG: 'pid-label pid-label--instrument',
  EQUIPMENT_TAG: 'pid-label pid-label--equipment',
  LINE_NUMBER: 'pid-label pid-label--line',
  DESCRIPTION: 'pid-label pid-label--desc',
  SERVICE: 'pid-label pid-label--service',
  ANNOTATION: 'pid-label pid-label--note',
  SPEC_REFERENCE: 'pid-label pid-label--spec',
  DEFAULT: 'pid-label',
};

/** Higher = shown first when space is tight */
const LABEL_PRIORITY = {
  INSTRUMENT_TAG: 100,
  EQUIPMENT_TAG: 98,
  LINE_NUMBER: 92,
  DESCRIPTION: 82,
  SERVICE: 78,
  ANNOTATION: 65,
  SPEC_REFERENCE: 60,
  PIPE_SIZE: 55,
  DRAWING_REFERENCE: 25,
  GRID_LABEL: 8,
  UNKNOWN: 5,
};

function labelPriority(classification) {
  return LABEL_PRIORITY[classification] ?? 30;
}

function toWorld(x, y, h) {
  return new THREE.Vector3(x, h - y, 0);
}

function centerOfBBox(bbox, h) {
  return toWorld(bbox.x + bbox.width / 2, bbox.y + bbox.height / 2, h);
}

function lineColor(type) {
  return LINE_COLORS[type] ?? LINE_COLORS.LIKELY_PIPE;
}

function objectColor(type) {
  return OBJECT_COLORS[type] ?? OBJECT_COLORS.DEFAULT;
}

function findEntity(id, { objects, texts, lines }) {
  return (
    objects.find((o) => o.id === id) ||
    texts.find((t) => t.id === id) ||
    lines.find((l) => l.id === id) ||
    null
  );
}

function entityPoint(entity, h) {
  if (!entity) return null;
  if (entity.bbox) return centerOfBBox(entity.bbox, h);
  if (entity.start && entity.end) {
    return toWorld(
      (entity.start[0] + entity.end[0]) / 2,
      (entity.start[1] + entity.end[1]) / 2,
      h
    );
  }
  return null;
}

function createSymbolMesh(obj, h) {
  const color = objectColor(obj.type);
  const w = Math.max(obj.bbox.width, 12);
  const ht = Math.max(obj.bbox.height, 12);
  const depth = Math.min(28, Math.max(10, Math.min(w, ht) * 0.4));

  let geometry;
  switch (obj.type) {
    case 'INSTRUMENT':
      geometry = new THREE.CylinderGeometry(Math.min(w, ht) / 2, Math.min(w, ht) / 2, depth, 28);
      geometry.rotateX(Math.PI / 2);
      break;
    case 'VALVE':
      geometry = new THREE.OctahedronGeometry(Math.min(w, ht) * 0.55, 0);
      break;
    case 'PUMP':
      geometry = new THREE.SphereGeometry(Math.min(w, ht) / 2, 24, 18);
      break;
    case 'TANK':
      geometry = new THREE.CylinderGeometry(w / 2.2, w / 2.2, ht, 28);
      geometry.rotateX(Math.PI / 2);
      break;
    case 'FLANGE':
      geometry = new THREE.CylinderGeometry(Math.max(w, ht) / 2, Math.max(w, ht) / 2, depth * 0.5, 16);
      geometry.rotateX(Math.PI / 2);
      break;
    default:
      geometry = new THREE.BoxGeometry(w, ht, depth);
  }

  const material = new THREE.MeshStandardMaterial({
    color,
    metalness: 0.22,
    roughness: 0.48,
    transparent: true,
    opacity: 0.95,
    emissive: 0x000000,
  });

  const mesh = new THREE.Mesh(geometry, material);
  const c = centerOfBBox(obj.bbox, h);
  mesh.position.set(c.x, c.y, depth / 2 + 2);

  const edge = new THREE.LineSegments(
    new THREE.EdgesGeometry(geometry),
    new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.28 })
  );
  mesh.add(edge);

  mesh.userData = {
    kind: 'OBJECT',
    entity: { ...obj, kind: 'OBJECT' },
    baseColor: color,
    visual: mesh,
  };
  return mesh;
}

function createTextLabel(txt, h, onSelect) {
  const el = document.createElement('button');
  el.type = 'button';
  el.className = TEXT_CLASS[txt.classification] || TEXT_CLASS.DEFAULT;
  el.textContent = txt.text;
  el.title = `${txt.id} · ${txt.classification}`;
  el.addEventListener('pointerdown', (e) => {
    e.stopPropagation();
    onSelect({ ...txt, kind: 'TEXT' });
  });

  const label = new CSS2DObject(el);
  const c = centerOfBBox(txt.bbox, h);
  label.position.set(c.x, c.y, 48);
  label.userData = {
    kind: 'TEXT',
    entity: { ...txt, kind: 'TEXT' },
    priority: labelPriority(txt.classification),
    confidence: txt.confidence ?? 0.5,
  };
  label.visible = false;
  el.style.display = 'none';
  return label;
}

function createPipeLine(line, h) {
  const a = toWorld(line.start[0], line.start[1], h);
  const b = toWorld(line.end[0], line.end[1], h);
  a.z = 4;
  b.z = 4;

  const isBorder = line.line_type === 'BORDER';
  const isDim = line.line_type === 'DIMENSION';
  const color = lineColor(line.line_type);
  const entity = { ...line, kind: 'LINE' };

  if (isDim) {
    const geometry = new THREE.BufferGeometry().setFromPoints([a, b]);
    const material = new THREE.LineDashedMaterial({
      color,
      dashSize: 18,
      gapSize: 12,
    });
    const mesh = new THREE.Line(geometry, material);
    mesh.computeLineDistances();

    const mid = a.clone().add(b).multiplyScalar(0.5);
    const len = a.distanceTo(b);
    const hit = new THREE.Mesh(
      new THREE.BoxGeometry(Math.max(len, 1), 8, 4),
      new THREE.MeshBasicMaterial({ visible: false })
    );
    hit.position.copy(mid);
    hit.rotation.z = Math.atan2(b.y - a.y, b.x - a.x);
    hit.userData = { kind: 'LINE', entity, visual: mesh };
    mesh.userData = { kind: 'LINE', entity, visual: mesh, baseColor: color };
    mesh.add(hit);
    return { mesh, hit };
  }

  const radius = isBorder ? 5 : 3.2;
  const curve = new THREE.LineCurve3(a, b);
  const tubular = Math.max(2, Math.ceil(a.distanceTo(b) / 80));
  const geometry = new THREE.TubeGeometry(curve, tubular, radius, 8, false);
  const material = new THREE.MeshStandardMaterial({
    color,
    metalness: 0.35,
    roughness: 0.4,
    emissive: 0x000000,
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.userData = { kind: 'LINE', entity, visual: mesh, baseColor: color };
  return { mesh, hit: mesh };
}

function createLinkLine(from, to, h, rel) {
  const a = entityPoint(from, h);
  const b = entityPoint(to, h);
  if (!a || !b) return null;
  a.z = 14;
  b.z = 14;

  // raised arc so links read above pipes
  const mid = a.clone().add(b).multiplyScalar(0.5);
  mid.z = 36;
  const curve = new THREE.QuadraticBezierCurve3(a, mid, b);
  const geometry = new THREE.TubeGeometry(curve, 16, 1.4, 6, false);
  const material = new THREE.MeshStandardMaterial({
    color: 0xb45309,
    metalness: 0.1,
    roughness: 0.55,
    transparent: true,
    opacity: 0.75,
    emissive: 0x000000,
  });
  const mesh = new THREE.Mesh(geometry, material);
  const entity = {
    ...rel,
    kind: 'RELATIONSHIP',
    id: `${rel.from_id}→${rel.to_id}`,
  };
  mesh.userData = { kind: 'LINK', entity, visual: mesh, baseColor: 0xb45309 };
  return { mesh, hit: mesh };
}

function createSheet(width, height) {
  const group = new THREE.Group();

  const paper = new THREE.Mesh(
    new THREE.PlaneGeometry(width, height),
    new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.92, metalness: 0.02 })
  );
  paper.position.set(width / 2, height / 2, 0);
  paper.receiveShadow = true;
  group.add(paper);

  // soft drop shadow under sheet
  const shadow = new THREE.Mesh(
    new THREE.PlaneGeometry(width + 40, height + 40),
    new THREE.MeshBasicMaterial({ color: 0xb8c0c8, transparent: true, opacity: 0.35 })
  );
  shadow.position.set(width / 2 + 18, height / 2 - 18, -2);
  group.add(shadow);

  const framePts = [
    new THREE.Vector3(24, 24, 1),
    new THREE.Vector3(width - 24, 24, 1),
    new THREE.Vector3(width - 24, height - 24, 1),
    new THREE.Vector3(24, height - 24, 1),
    new THREE.Vector3(24, 24, 1),
  ];
  group.add(
    new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(framePts),
      new THREE.LineBasicMaterial({ color: 0xcfd5dc })
    )
  );

  const gridStep = 200;
  const gridMat = new THREE.LineBasicMaterial({ color: 0xe8ecf0, transparent: true, opacity: 0.85 });
  for (let x = 0; x <= width; x += gridStep) {
    group.add(
      new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(x, 0, 0.4),
          new THREE.Vector3(x, height, 0.4),
        ]),
        gridMat
      )
    );
  }
  for (let y = 0; y <= height; y += gridStep) {
    group.add(
      new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(0, y, 0.4),
          new THREE.Vector3(width, y, 0.4),
        ]),
        gridMat
      )
    );
  }

  return group;
}

function createSelectionRing() {
  const ring = new THREE.Mesh(
    new THREE.RingGeometry(28, 36, 48),
    new THREE.MeshBasicMaterial({
      color: 0x0f6e56,
      transparent: true,
      opacity: 0.85,
      side: THREE.DoubleSide,
      depthTest: false,
    })
  );
  ring.visible = false;
  ring.renderOrder = 10;
  return ring;
}

/**
 * Mount a full P&ID Three.js scene into `container`.
 * Returns { api, dispose }.
 */
export function createPidScene(container, data, handlers = {}) {
  const { drawing, texts, objects, lines, relationships } = data;
  const W = drawing.resolution.width;
  const H = drawing.resolution.height;
  const onSelect = handlers.onSelect || (() => {});
  const onZoomChange = handlers.onZoomChange || (() => {});
  const onViewChange = handlers.onViewChange || (() => {});

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xe8ecf0);

  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 20000);
  camera.position.set(W / 2, H / 2, 1200);
  camera.lookAt(W / 2, H / 2, 0);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.domElement.style.display = 'block';
  renderer.domElement.style.width = '100%';
  renderer.domElement.style.height = '100%';
  renderer.domElement.style.touchAction = 'none';
  container.appendChild(renderer.domElement);

  const labelRenderer = new CSS2DRenderer();
  labelRenderer.setSize(container.clientWidth, container.clientHeight);
  labelRenderer.domElement.style.position = 'absolute';
  labelRenderer.domElement.style.inset = '0';
  labelRenderer.domElement.style.pointerEvents = 'none';
  container.appendChild(labelRenderer.domElement);

  scene.add(new THREE.AmbientLight(0xffffff, 0.78));
  const key = new THREE.DirectionalLight(0xffffff, 0.7);
  key.position.set(W * 0.2, H * 1.1, 900);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xdbe4ee, 0.35);
  fill.position.set(-W * 0.4, -H * 0.2, 500);
  scene.add(fill);
  const rim = new THREE.DirectionalLight(0xffffff, 0.2);
  rim.position.set(W, H * 0.5, 300);
  scene.add(rim);

  const root = new THREE.Group();
  scene.add(root);
  root.add(createSheet(W, H));

  const linesGroup = new THREE.Group();
  const objectsGroup = new THREE.Group();
  const textsGroup = new THREE.Group();
  const linksGroup = new THREE.Group();
  root.add(linesGroup, linksGroup, objectsGroup, textsGroup);

  const selectionRing = createSelectionRing();
  root.add(selectionRing);

  const pickables = [];
  const focusTargets = new Map();
  const textLabelEntries = [];
  const badgeLabels = [];
  const objectEntries = [];
  let layerState = { texts: true, objects: true, lines: true, links: true };
  let labelDensity = handlers.labelDensity || 'clean';
  let selectedEntityId = null;
  let visibleLabelCount = 0;

  lines.forEach((line) => {
    const built = createPipeLine(line, H);
    linesGroup.add(built.mesh);
    pickables.push(built.hit);
    const mid = toWorld(
      (line.start[0] + line.end[0]) / 2,
      (line.start[1] + line.end[1]) / 2,
      H
    );
    focusTargets.set(line.id, mid);
  });

  objects.forEach((obj) => {
    const mesh = createSymbolMesh(obj, H);
    objectsGroup.add(mesh);
    pickables.push(mesh);
    objectEntries.push({ mesh, type: obj.type, id: obj.id });
    focusTargets.set(obj.id, centerOfBBox(obj.bbox, H));
  });

  texts.forEach((txt) => {
    const label = createTextLabel(txt, H, (entity) => {
      focusOn(entity);
      selectMesh(null, entity);
      placeRingAt(focusTargets.get(entity.id));
    });
    textLabelEntries.push({
      label,
      id: txt.id,
      priority: labelPriority(txt.classification),
      confidence: txt.confidence ?? 0,
    });
    textsGroup.add(label);
    focusTargets.set(txt.id, centerOfBBox(txt.bbox, H));
  });

  relationships.forEach((rel) => {
    const from = findEntity(rel.from_id, { objects, texts, lines });
    const to = findEntity(rel.to_id, { objects, texts, lines });
    const built = createLinkLine(from, to, H, rel);
    if (built) {
      linksGroup.add(built.mesh);
      pickables.push(built.hit);
      const p = entityPoint(from, H)?.clone().add(entityPoint(to, H)).multiplyScalar(0.5);
      if (p) focusTargets.set(built.mesh.userData.entity.id, p);
    }
  });

  // Symbol type badges — hidden by default; declutter shows sparingly at high zoom
  objects.forEach((obj) => {
    const badge = document.createElement('div');
    badge.className = 'pid-symbol-badge';
    badge.textContent = obj.type;
    const label = new CSS2DObject(badge);
    const c = centerOfBBox(obj.bbox, H);
    label.position.set(c.x, c.y + obj.bbox.height / 2 + 22, 52);
    label.visible = false;
    badge.style.display = 'none';
    badgeLabels.push({ label, type: obj.type, id: obj.id });
    objectsGroup.add(label);
  });

  const raycaster = new THREE.Raycaster();
  // tubes need a bit of threshold help via params
  raycaster.params.Line = { threshold: 8 };
  const pointer = new THREE.Vector2();
  let selectedMesh = null;
  let hoveredMesh = null;
  let tiltEnabled = false;
  let tiltT = 0;

  function emitView() {
    const { clientWidth: cw, clientHeight: ch } = container;
    onViewChange({
      cx: camera.position.x,
      cy: camera.position.y,
      halfW: cw / (2 * camera.zoom),
      halfH: ch / (2 * camera.zoom),
      zoom: camera.zoom,
      drawingW: W,
      drawingH: H,
      visibleLabels: visibleLabelCount,
      totalLabels: textLabelEntries.length,
    });
  }

  function updateDeclutter() {
    const zoom = camera.zoom;
    const { clientWidth: cw, clientHeight: ch } = container;

    // Links only when zoomed in
    linksGroup.visible = layerState.links && zoom > 0.14;

    // Symbol LOD — hide tiny / noisy types at overview
    if (layerState.objects) {
      objectEntries.forEach(({ mesh, type }) => {
        if (type === 'FLANGE' && zoom < 0.22) mesh.visible = false;
        else if (type === 'INSTRUMENT' && zoom < 0.14) mesh.visible = false;
        else mesh.visible = true;
      });
    }

    // Badges only for major equipment when zoomed in
    badgeLabels.forEach(({ label, type, id }) => {
      const el = label.element;
      const isSelected = id === selectedEntityId;
      const show =
        isSelected && zoom > 0.2
          ? true
          : zoom > 0.5 && !['FLANGE', 'INSTRUMENT'].includes(type);
      label.visible = show;
      el.style.display = show ? '' : 'none';
    });

    if (!layerState.texts || !textsGroup.visible) {
      textLabelEntries.forEach((e) => {
        e.label.visible = false;
        e.label.element.style.display = 'none';
      });
      visibleLabelCount = 0;
      return;
    }

    if (!cw || !ch) return;

    const halfW = cw / (2 * zoom);
    const halfH = ch / (2 * zoom);
    const minX = camera.position.x - halfW;
    const maxX = camera.position.x + halfW;
    const minY = camera.position.y - halfH;
    const maxY = camera.position.y + halfH;
    const cellSize = Math.max(50, 320 / zoom);

    const densityCfg = {
      clean: {
        minP: zoom < 0.12 ? 90 : zoom < 0.22 ? 75 : zoom < 0.4 ? 50 : 20,
        maxCell: zoom < 0.1 ? 1 : zoom < 0.18 ? 2 : zoom < 0.35 ? 3 : zoom < 0.6 ? 8 : 24,
      },
      balanced: {
        minP: zoom < 0.1 ? 80 : zoom < 0.2 ? 45 : 10,
        maxCell: zoom < 0.08 ? 1 : zoom < 0.15 ? 3 : zoom < 0.35 ? 8 : 40,
      },
      all: { minP: 0, maxCell: 200 },
    };
    const cfg = densityCfg[labelDensity] || densityCfg.clean;

    textLabelEntries.forEach((e) => {
      e.label.visible = false;
      e.label.element.style.display = 'none';
    });

    const occupied = new Map();
    const candidates = textLabelEntries
      .filter((e) => {
        const p = e.label.position;
        if (p.x < minX - 80 || p.x > maxX + 80 || p.y < minY - 80 || p.y > maxY + 80) return false;
        if (e.id === selectedEntityId) return true;
        return e.priority >= cfg.minP;
      })
      .sort((a, b) => {
        if (a.id === selectedEntityId) return -1;
        if (b.id === selectedEntityId) return 1;
        return b.priority - a.priority || b.confidence - a.confidence;
      });

    let shown = 0;
    for (const e of candidates) {
      if (e.id === selectedEntityId) {
        e.label.visible = true;
        e.label.element.style.display = '';
        shown++;
        continue;
      }
      const cx = Math.floor(e.label.position.x / cellSize);
      const cy = Math.floor(e.label.position.y / cellSize);
      const key = `${cx},${cy}`;
      const n = occupied.get(key) || 0;
      if (n >= cfg.maxCell) continue;
      occupied.set(key, n + 1);
      e.label.visible = true;
      e.label.element.style.display = '';
      shown++;
    }
    visibleLabelCount = shown;
  }

  function clearHighlight(mesh) {
    const visual = mesh?.userData?.visual || mesh;
    if (!visual?.material) return;
    if (visual.material.emissive) visual.material.emissive.setHex(0x000000);
    if (visual.userData?.baseColor != null && visual.material.color) {
      visual.material.color.setHex(visual.userData.baseColor);
    }
    visual.scale.set(1, 1, 1);
  }

  function setHighlight(mesh, strong) {
    const visual = mesh?.userData?.visual || mesh;
    if (!visual?.material) return;
    if (visual.material.emissive) {
      visual.material.emissive.setHex(strong ? 0x0f6e56 : 0x3f4b5a);
      visual.material.emissiveIntensity = strong ? 0.55 : 0.25;
    }
    visual.scale.setScalar(strong ? 1.06 : 1.03);
  }

  function placeRingAt(point) {
    if (!point) {
      selectionRing.visible = false;
      return;
    }
    selectionRing.visible = true;
    selectionRing.position.set(point.x, point.y, 30);
  }

  function selectMesh(mesh, entity) {
    if (selectedMesh) clearHighlight(selectedMesh);
    selectedMesh = mesh || null;
    selectedEntityId = entity?.id ?? null;
    if (selectedMesh) setHighlight(selectedMesh, true);
    onSelect(entity || null);
    if (entity?.id && focusTargets.has(entity.id)) placeRingAt(focusTargets.get(entity.id));
    else if (!entity) selectionRing.visible = false;
    updateDeclutter();
    emitView();
  }

  function focusOn(entity) {
    if (!entity?.id) return;
    const p = focusTargets.get(entity.id);
    if (!p) return;
    camera.position.x = p.x;
    camera.position.y = p.y;
    camera.zoom = Math.max(camera.zoom, 0.35);
    camera.updateProjectionMatrix();
    onZoomChange(camera.zoom);
    updateDeclutter();
    emitView();
  }

  function fitView() {
    const { clientWidth: cw, clientHeight: ch } = container;
    if (!cw || !ch) return;
    const margin = 1.1;
    camera.zoom = Math.min(cw / (W * margin), ch / (H * margin));
    camera.position.x = W / 2;
    camera.position.y = H / 2;
    camera.position.z = tiltEnabled ? 1800 : 1200;
    camera.updateProjectionMatrix();
    onZoomChange(camera.zoom);
    updateDeclutter();
    emitView();
  }

  function updateFrustum() {
    const { clientWidth: cw, clientHeight: ch } = container;
    if (!cw || !ch) return;
    camera.left = -cw / 2;
    camera.right = cw / 2;
    camera.top = ch / 2;
    camera.bottom = -ch / 2;
    camera.updateProjectionMatrix();
  }

  updateFrustum();
  fitView();
  updateDeclutter();

  let dragging = false;
  let lastX = 0;
  let lastY = 0;
  let moved = false;

  const onPointerDown = (e) => {
    dragging = true;
    moved = false;
    lastX = e.clientX;
    lastY = e.clientY;
    renderer.domElement.setPointerCapture(e.pointerId);
  };

  const onPointerMove = (e) => {
    const rect = renderer.domElement.getBoundingClientRect();
    pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    if (dragging) {
      const dx = e.clientX - lastX;
      const dy = e.clientY - lastY;
      if (Math.abs(dx) + Math.abs(dy) > 2) moved = true;
      lastX = e.clientX;
      lastY = e.clientY;
      camera.position.x -= dx / camera.zoom;
      camera.position.y += dy / camera.zoom;
      updateDeclutter();
      emitView();
      return;
    }

    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObjects(pickables, false);
    const hit = hits[0]?.object;
    if (hoveredMesh && hoveredMesh !== selectedMesh) clearHighlight(hoveredMesh);
    hoveredMesh = hit || null;
    if (hoveredMesh && hoveredMesh !== selectedMesh) setHighlight(hoveredMesh, false);
    renderer.domElement.style.cursor = hit ? 'pointer' : 'grab';
  };

  const onPointerUp = (e) => {
    dragging = false;
    renderer.domElement.releasePointerCapture?.(e.pointerId);
    renderer.domElement.style.cursor = 'grab';
    if (moved) return;

    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObjects(pickables, false);
    if (hits[0]) {
      const mesh = hits[0].object;
      selectMesh(mesh, mesh.userData.entity);
    } else {
      selectMesh(null, null);
    }
  };

  const onWheel = (e) => {
    e.preventDefault();
    const factor = e.deltaY > 0 ? 0.9 : 1.1;
    const next = Math.min(Math.max(camera.zoom * factor, 0.04), 5);
    const rect = renderer.domElement.getBoundingClientRect();
    const mx = e.clientX - rect.left - rect.width / 2;
    const my = -(e.clientY - rect.top - rect.height / 2);
    const wxBefore = camera.position.x + mx / camera.zoom;
    const wyBefore = camera.position.y + my / camera.zoom;
    camera.zoom = next;
    camera.updateProjectionMatrix();
    camera.position.x = wxBefore - mx / camera.zoom;
    camera.position.y = wyBefore - my / camera.zoom;
    onZoomChange(camera.zoom);
    updateDeclutter();
    emitView();
  };

  renderer.domElement.addEventListener('pointerdown', onPointerDown);
  renderer.domElement.addEventListener('pointermove', onPointerMove);
  renderer.domElement.addEventListener('pointerup', onPointerUp);
  renderer.domElement.addEventListener('pointercancel', onPointerUp);
  renderer.domElement.addEventListener('wheel', onWheel, { passive: false });
  renderer.domElement.style.cursor = 'grab';

  const onResize = () => {
    renderer.setSize(container.clientWidth, container.clientHeight);
    labelRenderer.setSize(container.clientWidth, container.clientHeight);
    updateFrustum();
    onZoomChange(camera.zoom);
    updateDeclutter();
    emitView();
  };
  const ro = new ResizeObserver(onResize);
  ro.observe(container);

  let raf = 0;
  const clock = new THREE.Clock();
  const tick = () => {
    raf = requestAnimationFrame(tick);
    const dt = clock.getDelta();
    const targetTilt = tiltEnabled ? 1 : 0;
    tiltT += (targetTilt - tiltT) * Math.min(1, dt * 6);
    root.rotation.x = THREE.MathUtils.degToRad(-38) * tiltT;
    root.rotation.z = THREE.MathUtils.degToRad(18) * tiltT;
    if (selectionRing.visible) {
      selectionRing.rotation.z += dt * 0.8;
      selectionRing.scale.setScalar(1 + Math.sin(clock.elapsedTime * 3) * 0.04);
    }
    camera.lookAt(camera.position.x, camera.position.y, 0);
    renderer.render(scene, camera);
    labelRenderer.render(scene, camera);
    // ponytail: declutter on pan/zoom only — not every frame
  };
  tick();

  const api = {
    fitView: () => {
      fitView();
      updateDeclutter();
    },
    zoomBy: (factor) => {
      camera.zoom = Math.min(Math.max(camera.zoom * factor, 0.04), 5);
      camera.updateProjectionMatrix();
      onZoomChange(camera.zoom);
      updateDeclutter();
      emitView();
    },
    setLayers: ({ texts: t, objects: o, lines: l, links }) => {
      layerState = { texts: t, objects: o, lines: l, links: links };
      textsGroup.visible = t;
      objectsGroup.visible = o;
      linesGroup.visible = l;
      updateDeclutter();
    },
    setLabelDensity: (mode) => {
      labelDensity = mode || 'clean';
      updateDeclutter();
      emitView();
    },
    setTilt: (enabled) => {
      tiltEnabled = !!enabled;
      camera.position.z = tiltEnabled ? 1800 : 1200;
    },
    selectById: (id) => {
      if (!id) {
        selectMesh(null, null);
        return;
      }
      const mesh = pickables.find((m) => m.userData?.entity?.id === id);
      const entity = mesh?.userData?.entity || texts.find((t) => t.id === id);
      if (entity) {
        focusOn(entity.kind ? entity : { ...entity, kind: 'TEXT', id });
        selectMesh(mesh || null, mesh?.userData?.entity || { ...entity, kind: 'TEXT' });
        placeRingAt(focusTargets.get(id));
      }
    },
    focusId: (id) => {
      const entity = { id };
      focusOn(entity);
      placeRingAt(focusTargets.get(id));
    },
    panTo: (nx, ny) => {
      camera.position.x = nx * W;
      camera.position.y = (1 - ny) * H;
      updateDeclutter();
      emitView();
    },
    getZoom: () => camera.zoom,
    getVisibleLabels: () => visibleLabelCount,
  };

  const dispose = () => {
    cancelAnimationFrame(raf);
    ro.disconnect();
    renderer.domElement.removeEventListener('pointerdown', onPointerDown);
    renderer.domElement.removeEventListener('pointermove', onPointerMove);
    renderer.domElement.removeEventListener('pointerup', onPointerUp);
    renderer.domElement.removeEventListener('pointercancel', onPointerUp);
    renderer.domElement.removeEventListener('wheel', onWheel);
    labelRenderer.domElement.remove();
    renderer.dispose();
    renderer.domElement.remove();
    scene.traverse((obj) => {
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) {
        if (Array.isArray(obj.material)) obj.material.forEach((m) => m.dispose());
        else obj.material.dispose();
      }
    });
  };

  return { api, dispose };
}

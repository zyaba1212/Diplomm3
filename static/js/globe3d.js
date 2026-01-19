// static/js/globe3d.js
// Z96A Network Architecture Visualization
// Three.js 3D Globe with Network Infrastructure

class NetworkGlobe {
    constructor(containerId) {
        console.log('Initializing NetworkGlobe...');
        
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error('Container not found:', containerId);
            return;
        }
        
        // Конфигурация
        this.config = {
            earthRadius: 3.0,
            autoRotate: true,
            rotationSpeed: 0.001,
            showEquipment: true,
            showCables: true,
            currentNetwork: 'existing',
            zoomLevel: 1.0
        };
        
        // Данные
        this.nodes = [];
        this.connections = [];
        this.equipment = [];
        this.networkLayers = {
            existing: { nodes: [], connections: [], visible: true },
            proposed: { nodes: [], connections: [], visible: false },
            hybrid: { nodes: [], connections: [], visible: false }
        };
        
        // Инициализация
        this.initThreeJS();
        this.createEarth();
        this.loadNetworkData();
        this.createControls();
        
        console.log('NetworkGlobe ready');
    }
    
    initThreeJS() {
        // Сцена
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0a0a1a);
        this.scene.fog = new THREE.Fog(0x0a0a1a, 10, 50);
        
        // Камера
        this.camera = new THREE.PerspectiveCamera(
            75,
            this.container.clientWidth / this.container.clientHeight,
            0.1,
            1000
        );
        this.camera.position.set(0, 2, 8);
        
        // Рендерер
        this.renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: true,
            powerPreference: "high-performance"
        });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.container.appendChild(this.renderer.domElement);
        
        // Освещение
        this.setupLighting();
        
        // Звёздное небо
        this.createStarfield();
        
        // Анимация
        this.clock = new THREE.Clock();
        this.animate();
        
        // Ресайз
        window.addEventListener('resize', () => this.onWindowResize());
        
        // Клики по объектам
        this.setupRaycaster();
    }
    
    setupLighting() {
        // Основное освещение
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
        this.scene.add(ambientLight);
        
        // Солнце (основной источник)
        const sunLight = new THREE.DirectionalLight(0xffffff, 0.8);
        sunLight.position.set(10, 10, 10);
        sunLight.castShadow = true;
        sunLight.shadow.mapSize.width = 2048;
        sunLight.shadow.mapSize.height = 2048;
        this.scene.add(sunLight);
        
        // Заполняющий свет
        const fillLight = new THREE.DirectionalLight(0x4466ff, 0.3);
        fillLight.position.set(-10, 5, -10);
        this.scene.add(fillLight);
    }
    
    createStarfield() {
        const starGeometry = new THREE.BufferGeometry();
        const starCount = 5000;
        const positions = new Float32Array(starCount * 3);
        
        for (let i = 0; i < starCount * 3; i += 3) {
            positions[i] = (Math.random() - 0.5) * 100;
            positions[i + 1] = (Math.random() - 0.5) * 100;
            positions[i + 2] = (Math.random() - 0.5) * 100;
        }
        
        starGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        
        const starMaterial = new THREE.PointsMaterial({
            color: 0xffffff,
            size: 0.1,
            transparent: true
        });
        
        const stars = new THREE.Points(starGeometry, starMaterial);
        this.scene.add(stars);
    }
    
    async createEarth() {
        try {
            // Создаём Землю с текстурами
            const geometry = new THREE.SphereGeometry(this.config.earthRadius, 64, 64);
            
            // Загружаем текстуры
            const textureLoader = new THREE.TextureLoader();
            const earthTexture = textureLoader.load('/static/images/earth_texture.jpg');
            const bumpMap = textureLoader.load('/static/images/earth_bump.jpg');
            const specularMap = textureLoader.load('/static/images/earth_lights.jpg');
            
            const material = new THREE.MeshPhongMaterial({
                map: earthTexture,
                bumpMap: bumpMap,
                bumpScale: 0.05,
                specularMap: specularMap,
                specular: new THREE.Color(0x333333),
                shininess: 5,
                emissive: new THREE.Color(0x0a1a2a),
                emissiveIntensity: 0.1
            });
            
            this.earth = new THREE.Mesh(geometry, material);
            this.earth.receiveShadow = true;
            this.scene.add(this.earth);
            
            // Атмосфера
            const atmosphereGeometry = new THREE.SphereGeometry(this.config.earthRadius * 1.02, 64, 64);
            const atmosphereMaterial = new THREE.MeshPhongMaterial({
                color: 0x4466ff,
                transparent: true,
                opacity: 0.1,
                side: THREE.BackSide
            });
            
            this.atmosphere = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial);
            this.scene.add(this.atmosphere);
            
            // Облака
            const cloudGeometry = new THREE.SphereGeometry(this.config.earthRadius * 1.01, 64, 64);
            const cloudMaterial = new THREE.MeshPhongMaterial({
                color: 0xffffff,
                transparent: true,
                opacity: 0.2,
                side: THREE.DoubleSide
            });
            
            this.clouds = new THREE.Mesh(cloudGeometry, cloudMaterial);
            this.scene.add(this.clouds);
            
            console.log('Earth created with textures');
            
        } catch (error) {
            console.error('Error creating Earth:', error);
            // Fallback: простая Земля без текстур
            const geometry = new THREE.SphereGeometry(this.config.earthRadius, 32, 32);
            const material = new THREE.MeshPhongMaterial({
                color: 0x1a5fb4,
                specular: 0x111111,
                shininess: 30
            });
            
            this.earth = new THREE.Mesh(geometry, material);
            this.scene.add(this.earth);
        }
    }
    
    async loadNetworkData() {
        try {
            const response = await fetch('/static/data/network_data.json');
            const data = await response.json();
            
            console.log('Network data loaded:', data);
            
            // Создаём сетевые объекты
            this.createNetworkNodes(data.nodes || []);
            this.createNetworkConnections(data.connections || []);
            this.createNetworkEquipment(data.equipment || []);
            
        } catch (error) {
            console.error('Error loading network data:', error);
            this.createSampleNetwork();
        }
    }
    
    createNetworkNodes(nodes) {
        nodes.forEach(node => {
            const position = this.latLonToVector(node.latitude, node.longitude, this.config.earthRadius * 1.05);
            
            // Создаём маркер узла
            let geometry, material;
            
            switch(node.type) {
                case 'datacenter':
                    geometry = new THREE.ConeGeometry(0.05, 0.1, 8);
                    material = new THREE.MeshPhongMaterial({ color: 0xff4444, emissive: 0x441111 });
                    break;
                case 'ix':
                    geometry = new THREE.BoxGeometry(0.07, 0.07, 0.07);
                    material = new THREE.MeshPhongMaterial({ color: 0x44ff44, emissive: 0x114411 });
                    break;
                case 'city':
                    geometry = new THREE.SphereGeometry(0.04, 8, 8);
                    material = new THREE.MeshPhongMaterial({ color: 0x4444ff, emissive: 0x111144 });
                    break;
                default:
                    geometry = new THREE.SphereGeometry(0.03, 8, 8);
                    material = new THREE.MeshPhongMaterial({ color: 0xffff44 });
            }
            
            const marker = new THREE.Mesh(geometry, material);
            marker.position.copy(position);
            marker.userData = node;
            marker.castShadow = true;
            
            // Добавляем в соответствующий слой
            if (node.network_type === 'proposed') {
                this.networkLayers.proposed.nodes.push(marker);
                marker.visible = false;
            } else {
                this.networkLayers.existing.nodes.push(marker);
            }
            
            this.scene.add(marker);
            this.nodes.push(marker);
            
            // Добавляем свечение
            this.addNodeGlow(position, node.type);
        });
    }
    
    createNetworkConnections(connections) {
        connections.forEach(conn => {
            const fromPos = this.latLonToVector(conn.from.lat, conn.from.lon, this.config.earthRadius * 1.03);
            const toPos = this.latLonToVector(conn.to.lat, conn.to.lon, this.config.earthRadius * 1.03);
            
            // Создаём кривую Безье для кабеля
            const curve = new THREE.CubicBezierCurve3(
                fromPos,
                new THREE.Vector3(
                    (fromPos.x + toPos.x) / 2 + (Math.random() - 0.5) * 0.5,
                    (fromPos.y + toPos.y) / 2 + 0.3,
                    (fromPos.z + toPos.z) / 2 + (Math.random() - 0.5) * 0.5
                ),
                new THREE.Vector3(
                    (fromPos.x + toPos.x) / 2 + (Math.random() - 0.5) * 0.5,
                    (fromPos.y + toPos.y) / 2 + 0.3,
                    (fromPos.z + toPos.z) / 2 + (Math.random() - 0.5) * 0.5
                ),
                toPos
            );
            
            const points = curve.getPoints(50);
            const geometry = new THREE.BufferGeometry().setFromPoints(points);
            
            const material = new THREE.LineBasicMaterial({
                color: conn.type === 'undersea' ? 0x00ffff : 0xffff00,
                transparent: true,
                opacity: 0.7,
                linewidth: 2
            });
            
            const cable = new THREE.Line(geometry, material);
            cable.userData = conn;
            
            // Добавляем в соответствующий слой
            if (conn.network_type === 'proposed') {
                this.networkLayers.proposed.connections.push(cable);
                cable.visible = false;
            } else {
                this.networkLayers.existing.connections.push(cable);
            }
            
            this.scene.add(cable);
            this.connections.push(cable);
        });
    }
    
    createNetworkEquipment(equipmentList) {
        equipmentList.forEach(eq => {
            const position = this.latLonToVector(eq.latitude, eq.longitude, this.config.earthRadius * 1.08);
            
            let geometry, material;
            
            switch(eq.type) {
                case 'router':
                    geometry = new THREE.BoxGeometry(0.06, 0.04, 0.08);
                    material = new THREE.MeshPhongMaterial({ color: 0xff6600 });
                    break;
                case 'switch':
                    geometry = new THREE.BoxGeometry(0.08, 0.02, 0.06);
                    material = new THREE.MeshPhongMaterial({ color: 0x00cc66 });
                    break;
                case 'server':
                    geometry = new THREE.BoxGeometry(0.05, 0.08, 0.05);
                    material = new THREE.MeshPhongMaterial({ color: 0x3366ff });
                    break;
                case 'satellite':
                    geometry = new THREE.OctahedronGeometry(0.04);
                    material = new THREE.MeshPhongMaterial({ color: 0xff33cc, emissive: 0x330033 });
                    break;
                default:
                    geometry = new THREE.BoxGeometry(0.04, 0.04, 0.04);
                    material = new THREE.MeshPhongMaterial({ color: 0x888888 });
            }
            
            const equipment = new THREE.Mesh(geometry, material);
            equipment.position.copy(position);
            equipment.userData = eq;
            equipment.castShadow = true;
            
            // Вращение оборудования
            equipment.rotation.y = Math.random() * Math.PI * 2;
            
            this.scene.add(equipment);
            this.equipment.push(equipment);
            
            if (!this.config.showEquipment) {
                equipment.visible = false;
            }
        });
    }
    
    addNodeGlow(position, type) {
        const glowGeometry = new THREE.SphereGeometry(0.08, 16, 16);
        const glowMaterial = new THREE.MeshBasicMaterial({
            color: type === 'datacenter' ? 0xff0000 : 0x00ff00,
            transparent: true,
            opacity: 0.3,
            side: THREE.BackSide
        });
        
        const glow = new THREE.Mesh(glowGeometry, glowMaterial);
        glow.position.copy(position);
        this.scene.add(glow);
    }
    
    createSampleNetwork() {
        console.log('Creating sample network data...');
        
        const sampleNodes = [
            { name: "Москва", latitude: 55.7558, longitude: 37.6173, type: "datacenter", network_type: "existing" },
            { name: "Франкфурт", latitude: 50.1109, longitude: 8.6821, type: "ix", network_type: "existing" },
            { name: "Сингапур", latitude: 1.3521, longitude: 103.8198, type: "datacenter", network_type: "existing" },
            { name: "Нью-Йорк", latitude: 40.7128, longitude: -74.0060, type: "city", network_type: "existing" },
            { name: "Токио", latitude: 35.6762, longitude: 139.6503, type: "city", network_type: "existing" },
            // Предлагаемая сеть
            { name: "Starlink Gateway", latitude: 51.5074, longitude: -0.1278, type: "satellite", network_type: "proposed" },
            { name: "SUI Relay Node", latitude: 48.8566, longitude: 2.3522, type: "router", network_type: "proposed" }
        ];
        
        const sampleConnections = [
            { from: { lat: 55.7558, lon: 37.6173 }, to: { lat: 50.1109, lon: 8.6821 }, type: "terrestrial", network_type: "existing" },
            { from: { lat: 50.1109, lon: 8.6821 }, to: { lat: 40.7128, lon: -74.0060 }, type: "undersea", network_type: "existing" },
            { from: { lat: 1.3521, lon: 103.8198 }, to: { lat: 35.6762, lon: 139.6503 }, type: "undersea", network_type: "existing" },
            // Предлагаемые соединения
            { from: { lat: 51.5074, lon: -0.1278 }, to: { lat: 40.7128, lon: -74.0060 }, type: "satellite", network_type: "proposed" }
        ];
        
        const sampleEquipment = [
            { name: "Cisco Router", latitude: 55.7558, longitude: 37.6173, type: "router" },
            { name: "Juniper Switch", latitude: 50.1109, longitude: 8.6821, type: "switch" },
            { name: "Dell Server", latitude: 1.3521, longitude: 103.8198, type: "server" },
            { name: "Starlink Dish", latitude: 51.5074, longitude: -0.1278, type: "satellite" }
        ];
        
        this.createNetworkNodes(sampleNodes);
        this.createNetworkConnections(sampleConnections);
        this.createNetworkEquipment(sampleEquipment);
    }
    
createControls() {
    if (!this.camera || !this.renderer) {
        console.error('Cannot create controls: camera or renderer not initialized');
        return;
    }
    
    this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    this.controls.rotateSpeed = 0.5;
    this.controls.minDistance = 4;
    this.controls.maxDistance = 20;
    
    if (this.config.autoRotate) {
        this.controls.autoRotate = true;
        this.controls.autoRotateSpeed = this.config.rotationSpeed * 50;
    }
    
    console.log('OrbitControls created');
}
    
    setupRaycaster() {
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        
        this.container.addEventListener('click', (event) => {
            this.mouse.x = (event.clientX / this.container.clientWidth) * 2 - 1;
            this.mouse.y = -(event.clientY / this.container.clientHeight) * 2 + 1;
            
            this.raycaster.setFromCamera(this.mouse, this.camera);
            
            // Проверяем клики по узлам
            const intersects = this.raycaster.intersectObjects(this.nodes.concat(this.equipment));
            
            if (intersects.length > 0) {
                const object = intersects[0].object;
                this.showObjectInfo(object.userData);
            }
        });
    }
    
    showObjectInfo(data) {
        // Создаём всплывающее окно с информацией
        const infoDiv = document.createElement('div');
        infoDiv.style.cssText = `
            position: absolute;
            top: 100px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(30, 30, 46, 0.95);
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #8a2be2;
            color: white;
            font-family: 'CGXYZ PC', monospace;
            z-index: 1000;
            max-width: 400px;
            box-shadow: 0 0 30px rgba(138, 43, 226, 0.5);
        `;
        
        infoDiv.innerHTML = `
            <h3 style="margin-top: 0; color: #00ffff;">${data.name || data.type}</h3>
            <p><strong>Тип:</strong> ${data.type}</p>
            ${data.latitude ? `<p><strong>Координаты:</strong> ${data.latitude.toFixed(4)}, ${data.longitude.toFixed(4)}</p>` : ''}
            ${data.network_type ? `<p><strong>Сеть:</strong> ${data.network_type}</p>` : ''}
            ${data.description ? `<p>${data.description}</p>` : ''}
            <button onclick="this.parentElement.remove()" style="background: #ff4444; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Закрыть</button>
        `;
        
        this.container.appendChild(infoDiv);
        
        // Автоудаление через 10 секунд
        setTimeout(() => {
            if (infoDiv.parentElement) {
                infoDiv.remove();
            }
        }, 10000);
    }
    
    latLonToVector(lat, lon, radius) {
        const phi = (90 - lat) * (Math.PI / 180);
        const theta = (lon + 180) * (Math.PI / 180);
        
        const x = -(radius * Math.sin(phi) * Math.cos(theta));
        const y = radius * Math.cos(phi);
        const z = radius * Math.sin(phi) * Math.sin(theta);
        
        return new THREE.Vector3(x, y, z);
    }
    
    // Публичные методы для управления
    toggleRotation() {
        this.config.autoRotate = !this.config.autoRotate;
        this.controls.autoRotate = this.config.autoRotate;
        console.log('Auto-rotation:', this.config.autoRotate ? 'ON' : 'OFF');
    }
    
    resetView() {
        this.controls.reset();
        this.camera.position.set(0, 2, 8);
        console.log('View reset');
    }
    
    zoomIn() {
        this.config.zoomLevel = Math.min(this.config.zoomLevel * 1.2, 3.0);
        this.camera.position.multiplyScalar(0.83);
        console.log('Zoom in:', this.config.zoomLevel.toFixed(2));
    }
    
    zoomOut() {
        this.config.zoomLevel = Math.max(this.config.zoomLevel / 1.2, 0.5);
        this.camera.position.multiplyScalar(1.2);
        console.log('Zoom out:', this.config.zoomLevel.toFixed(2));
    }
    
    toggleEquipment() {
        this.config.showEquipment = !this.config.showEquipment;
        this.equipment.forEach(eq => eq.visible = this.config.showEquipment);
        console.log('Equipment:', this.config.showEquipment ? 'SHOW' : 'HIDE');
    }
    
    toggleCables() {
        this.config.showCables = !this.config.showCables;
        this.connections.forEach(conn => conn.visible = this.config.showCables);
        console.log('Cables:', this.config.showCables ? 'SHOW' : 'HIDE');
    }
    
    switchNetwork(networkType) {
        console.log('Switching to network:', networkType);
        
        // Скрываем все слои
        Object.keys(this.networkLayers).forEach(key => {
            const layer = this.networkLayers[key];
            layer.nodes.forEach(node => node.visible = false);
            layer.connections.forEach(conn => conn.visible = false);
        });
        
        // Показываем выбранный слой
        if (this.networkLayers[networkType]) {
            this.networkLayers[networkType].nodes.forEach(node => node.visible = true);
            this.networkLayers[networkType].connections.forEach(conn => conn.visible = true);
        }
        
        // Для гибридной сети показываем оба слоя
        if (networkType === 'hybrid') {
            this.networkLayers.existing.nodes.forEach(node => node.visible = true);
            this.networkLayers.existing.connections.forEach(conn => conn.visible = true);
            this.networkLayers.proposed.nodes.forEach(node => node.visible = true);
            this.networkLayers.proposed.connections.forEach(conn => conn.visible = true);
        }
        
        this.config.currentNetwork = networkType;
    }
    
 animate() {
    requestAnimationFrame(() => this.animate());
    
    const delta = this.clock.getDelta();
    
    // Вращение Земли
    if (this.earth) {
        this.earth.rotation.y += this.config.rotationSpeed;
    }
    
    // Вращение облаков
    if (this.clouds) {
        this.clouds.rotation.y += this.config.rotationSpeed * 1.5;
    }
    
    // Вращение атмосферы
    if (this.atmosphere) {
        this.atmosphere.rotation.y += this.config.rotationSpeed * 0.5;
    }
    
    // Анимация оборудования
    this.equipment.forEach(eq => {
        eq.rotation.y += delta * 0.5;
    });
    
    if (this.controls) {
        this.controls.update();
    }
    
    // Рендер
    this.renderer.render(this.scene, this.camera);
}
}
// Глобальные методы для кнопок
window.NetworkGlobe = NetworkGlobe;
console.log('NetworkGlobe class loaded');
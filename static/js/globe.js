class NetworkGlobe {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.earth = null;
        this.clouds = null;
        this.satellites = [];
        this.equipment = [];
        this.connections = [];
        this.cables = [];
        this.cableLines = [];
        this.selectedElement = null;
        
        this.settings = {
            showExisting: true,
            showProposed: true,
            showSatellites: true,
            showStations: true,
            showRouters: true,
            showCables: true,
            zoomLevel: 50,
            isRotating: true
        };
        
        this.networkData = null;
        this.cableData = null;
        
        this.colors = {
            earth: 0x1a5fb4,
            existing: 0x6c63ff,
            proposed: 0x00ff9d,
            satellite: 0xf5f5f5,
            station: 0xffa348,
            router: 0xed333b,
            submarine_cable: 0x1e90ff,
            terrestrial_cable: 0x00ff9d
        };
        
        this.init();
    }
    
    async init() {
        await this.loadNetworkData();
        await this.loadCableData();
        this.setupScene();
        this.createEarth();
        this.createNetworkElements();
        this.createCables();
        this.setupControls();
        this.setupEventListeners();
        this.animate();
        this.updateCounters();
    }
    
    async loadNetworkData() {
        try {
            const response = await fetch('/ru/api/network-data/');
            this.networkData = await response.json();
            console.log('Network data loaded:', this.networkData);
        } catch (error) {
            console.error('Error loading network data:', error);
            this.loadDemoData();
        }
    }
    
    async loadCableData() {
        try {
            const response = await fetch('/static/data/cables.json');
            this.cableData = await response.json();
            console.log('Cable data loaded:', this.cableData.cables.length, 'cables');
        } catch (error) {
            console.error('Error loading cable data:', error);
            this.cableData = { cables: [] };
        }
    }
    
    loadDemoData() {
        this.networkData = {
            elements: [
                {
                    id: 'demo-sat1',
                    name: 'Starlink Satellite',
                    type: 'satellite',
                    network: 'existing',
                    lat: 40.7128,
                    lng: -74.0060,
                    alt: 550,
                    description: 'Low Earth orbit satellite'
                }
            ],
            connections: []
        };
    }
    
    setupScene() {
        const canvas = document.getElementById('globeCanvas');
        if (!canvas) return;
        
        this.scene = new THREE.Scene();
        this.scene.fog = new THREE.Fog(0x0a1a2d, 100, 1000);
        
        this.camera = new THREE.PerspectiveCamera(
            75,
            canvas.clientWidth / canvas.clientHeight,
            0.1,
            2000
        );
        this.camera.position.set(0, 0, 25);
        
        this.renderer = new THREE.WebGLRenderer({
            canvas,
            antialias: true,
            alpha: true
        });
        this.renderer.setSize(canvas.clientWidth, canvas.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.setClearColor(0x000000, 0);
        
        const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
        this.scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 10, 5);
        this.scene.add(directionalLight);
        
        this.createStarfield();
    }
    
    createStarfield() {
        const starGeometry = new THREE.BufferGeometry();
        const starCount = 5000;
        const positions = new Float32Array(starCount * 3);
        
        for (let i = 0; i < starCount * 3; i += 3) {
            positions[i] = (Math.random() - 0.5) * 2000;
            positions[i + 1] = (Math.random() - 0.5) * 2000;
            positions[i + 2] = (Math.random() - 0.5) * 2000;
        }
        
        starGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        
        const starMaterial = new THREE.PointsMaterial({
            color: 0xffffff,
            size: 0.7,
            transparent: true
        });
        
        const stars = new THREE.Points(starGeometry, starMaterial);
        this.scene.add(stars);
    }
    
    createEarth() {
        const earthGeometry = new THREE.SphereGeometry(10, 64, 64);
        const textureLoader = new THREE.TextureLoader();
        
        const earthTexture = textureLoader.load('https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/planets/earth_atmos_2048.jpg');
        const earthBump = textureLoader.load('https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/planets/earth_normal_2048.jpg');
        const earthSpec = textureLoader.load('https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/planets/earth_specular_2048.jpg');
        
        const earthMaterial = new THREE.MeshPhongMaterial({
            map: earthTexture,
            bumpMap: earthBump,
            bumpScale: 0.05,
            specularMap: earthSpec,
            specular: new THREE.Color(0x333333),
            shininess: 5
        });
        
        this.earth = new THREE.Mesh(earthGeometry, earthMaterial);
        this.scene.add(this.earth);
        
        const cloudGeometry = new THREE.SphereGeometry(10.1, 64, 64);
        const cloudTexture = textureLoader.load('https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/planets/earth_clouds_1024.png');
        
        const cloudMaterial = new THREE.MeshPhongMaterial({
            map: cloudTexture,
            transparent: true,
            opacity: 0.4
        });
        
        this.clouds = new THREE.Mesh(cloudGeometry, cloudMaterial);
        this.scene.add(this.clouds);
    }
    
    latLngAltToVector3(lat, lng, alt) {
        const phi = (90 - lat) * (Math.PI / 180);
        const theta = (lng + 180) * (Math.PI / 180);
        const radius = 10 + (alt / 1000);
        
        return new THREE.Vector3(
            -radius * Math.sin(phi) * Math.cos(theta),
            radius * Math.cos(phi),
            radius * Math.sin(phi) * Math.sin(theta)
        );
    }
    
    createNetworkElements() {
        if (!this.networkData) return;
        
        this.clearNetworkElements();
        
        this.networkData.elements.forEach(element => {
            if (!this.shouldShowElement(element)) return;
            
            const position = this.latLngAltToVector3(element.lat, element.lng, element.alt);
            const elementMesh = this.createElementMesh(element, position);
            
            if (elementMesh) {
                if (element.type !== 'satellite' && element.alt === 0) {
                    const surfacePos = position.clone().normalize().multiplyScalar(10.01);
                    elementMesh.position.copy(surfacePos);
                } else {
                    elementMesh.position.copy(position);
                }
                
                this.scene.add(elementMesh);
                elementMesh.userData = { 
                    ...element, 
                    originalPosition: position.clone(),
                    isSatellite: element.type === 'satellite'
                };
                
                this.equipment.push(elementMesh);
                
                if (element.type === 'satellite') {
                    this.satellites.push(elementMesh);
                }
            }
        });
        
        this.createConnections();
    }
    
    createElementMesh(element, position) {
        let geometry, material;
        let scale = 1;
        
        switch(element.type) {
            case 'satellite':
                geometry = new THREE.OctahedronGeometry(0.3, 0);
                material = new THREE.MeshPhongMaterial({
                    color: this.colors.satellite,
                    emissive: 0x222222,
                    shininess: 100
                });
                scale = 1.2;
                break;
            case 'ground_station':
                geometry = new THREE.ConeGeometry(0.2, 0.5, 8);
                material = new THREE.MeshPhongMaterial({
                    color: this.colors.station,
                    emissive: 0x222222
                });
                geometry.rotateX(Math.PI);
                break;
            case 'router':
            case 'core_router':
                geometry = new THREE.BoxGeometry(0.3, 0.3, 0.3);
                material = new THREE.MeshPhongMaterial({
                    color: this.colors.router,
                    emissive: 0x222222
                });
                break;
            default:
                geometry = new THREE.SphereGeometry(0.2, 8, 8);
                material = new THREE.MeshPhongMaterial({
                    color: this.colors.existing,
                    emissive: 0x222222
                });
        }
        
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.copy(position);
        mesh.scale.set(scale, scale, scale);
        
        return mesh;
    }
    
    createCables() {
        if (!this.cableData || !this.cableData.cables) return;
        
        console.log('Creating cables:', this.cableData.cables.length);
        
        this.cableData.cables.forEach(cable => {
            if (!this.settings.showCables) return;
            
            const color = cable.color || (cable.type === 'submarine' ? '#1e90ff' : '#00ff9d');
            const cableLine = this.createCableLine(cable.route, color);
            
            if (cableLine) {
                cableLine.userData = cable;
                this.scene.add(cableLine);
                this.cableLines.push(cableLine);
            }
        });
        
        console.log('Cables created:', this.cableLines.length);
    }
    
    createCableLine(route, color) {
        if (!route || route.length < 2) return null;
        
        const points = [];
        
        route.forEach(point => {
            const pos = this.latLngAltToVector3(point.lat, point.lng, 0);
            const lifted = pos.clone().normalize().multiplyScalar(10.05);
            points.push(lifted);
        });
        
        const curve = new THREE.CatmullRomCurve3(points);
        const curvePoints = curve.getPoints(100);
        
        const geometry = new THREE.BufferGeometry().setFromPoints(curvePoints);
        
        const material = new THREE.LineBasicMaterial({
            color: new THREE.Color(color),
            transparent: true,
            opacity: 0.8,
            linewidth: 2
        });
        
        return new THREE.Line(geometry, material);
    }
    
    createConnections() {
        if (!this.networkData || !this.networkData.connections) return;
        
        this.networkData.connections.forEach(conn => {
            const fromElement = this.findElementById(conn.from);
            const toElement = this.findElementById(conn.to);
            
            if (fromElement && toElement && this.shouldShowConnection(conn)) {
                const connection = this.createConnectionLine(
                    fromElement.userData.originalPosition,
                    toElement.userData.originalPosition,
                    conn.type
                );
                
                if (connection) {
                    this.scene.add(connection);
                    this.connections.push(connection);
                }
            }
        });
    }
    
    createConnectionLine(fromPos, toPos, type) {
        const curve = new THREE.CatmullRomCurve3([fromPos, toPos]);
        const points = curve.getPoints(50);
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        
        let color;
        switch(type) {
            case 'satellite_link':
                color = this.colors.proposed;
                break;
            case 'fiber':
                color = this.colors.existing;
                break;
            default:
                color = 0x888888;
        }
        
        const material = new THREE.LineBasicMaterial({
            color: color,
            transparent: true,
            opacity: 0.6
        });
        
        return new THREE.Line(geometry, material);
    }
    
    findElementById(id) {
        return this.equipment.find(el => el.userData.id === id);
    }
    
    shouldShowElement(element) {
        if (!this.settings.showExisting && element.network === 'existing') return false;
        if (!this.settings.showProposed && element.network === 'proposed') return false;
        
        switch(element.type) {
            case 'satellite':
                return this.settings.showSatellites;
            case 'ground_station':
                return this.settings.showStations;
            case 'router':
            case 'core_router':
                return this.settings.showRouters;
            default:
                return true;
        }
    }
    
    shouldShowConnection(connection) {
        return this.settings.showCables;
    }
    
    clearNetworkElements() {
        this.equipment.forEach(mesh => this.scene.remove(mesh));
        this.connections.forEach(conn => this.scene.remove(conn));
        this.cableLines.forEach(cable => this.scene.remove(cable));
        
        this.satellites = [];
        this.equipment = [];
        this.connections = [];
        this.cableLines = [];
    }
    
    setupControls() {
        const canvas = document.getElementById('globeCanvas');
        if (!canvas || !this.camera || !this.renderer) return;
        
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.minDistance = 15;
        this.controls.maxDistance = 100;
        
        this.setupRaycaster();
    }
    
    setupRaycaster() {
        const canvas = document.getElementById('globeCanvas');
        if (!canvas) return;
        
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();
        
        canvas.addEventListener('click', (event) => {
            const rect = canvas.getBoundingClientRect();
            mouse.x = ((event.clientX - rect.left) / canvas.clientWidth) * 2 - 1;
            mouse.y = -((event.clientY - rect.top) / canvas.clientHeight) * 2 + 1;
            
            raycaster.setFromCamera(mouse, this.camera);
            
            const intersects = raycaster.intersectObjects(this.equipment);
            
            if (intersects.length > 0) {
                this.selectElement(intersects[0].object.userData);
            } else {
                const cableIntersects = raycaster.intersectObjects(this.cableLines);
                if (cableIntersects.length > 0) {
                    this.selectCable(cableIntersects[0].object.userData);
                } else {
                    this.clearSelection();
                }
            }
        });
        
        canvas.addEventListener('mousemove', (event) => {
            const rect = canvas.getBoundingClientRect();
            mouse.x = ((event.clientX - rect.left) / canvas.clientWidth) * 2 - 1;
            mouse.y = -((event.clientY - rect.top) / canvas.clientHeight) * 2 + 1;
            
            raycaster.setFromCamera(mouse, this.camera);
            
            this.equipment.forEach(el => el.material.emissive.setHex(0x222222));
            
            const intersects = raycaster.intersectObjects([...this.equipment, ...this.cableLines]);
            
            if (intersects.length > 0) {
                if (intersects[0].object.type === 'Mesh') {
                    intersects[0].object.material.emissive.setHex(0x666666);
                }
                canvas.style.cursor = 'pointer';
            } else {
                canvas.style.cursor = 'grab';
            }
        });
    }
    
    selectElement(elementData) {
        this.selectedElement = elementData;
        this.showElementInfo(elementData);
        
        this.equipment.forEach(el => {
            if (el.userData.id === elementData.id) {
                el.material.emissive.setHex(0xffaa00);
            } else {
                el.material.emissive.setHex(0x222222);
            }
        });
    }
    
    selectCable(cableData) {
        this.showCableInfo(cableData);
    }
    
    clearSelection() {
        this.selectedElement = null;
        this.equipment.forEach(el => el.material.emissive.setHex(0x222222));
        this.clearElementInfo();
    }
    
    showElementInfo(data) {
        const infoPanel = document.getElementById('elementInfo');
        if (!infoPanel) return;
        
        infoPanel.innerHTML = `
            ${data.name}
            Тип: ${this.getElementTypeName(data.type)}
            Координаты: ${data.lat.toFixed(4)}°, ${data.lng.toFixed(4)}°
            ${data.description}
        `;
    }
    
    showCableInfo(cable) {
        const infoPanel = document.getElementById('elementInfo');
        if (!infoPanel) return;
        
        const owners = cable.owners ? cable.owners.join(', ') : 'Неизвестно';
        
        infoPanel.innerHTML = `
            ${cable.name}
            Тип: ${cable.type === 'submarine' ? 'Подводный' : 'Наземный'}
            Пропускная способность: ${cable.capacity || 'N/A'}
            Длина: ${cable.length || 'N/A'}
            Год: ${cable.year || 'N/A'}
            Владельцы: ${owners}
            ${cable.description}
        `;
    }
    
    clearElementInfo() {
        const infoPanel = document.getElementById('elementInfo');
        if (infoPanel) {
            infoPanel.innerHTML = 'Выберите элемент сети для получения информации';
        }
    }
    
    getElementTypeName(type) {
        const names = {
            'satellite': 'Спутник',
            'ground_station': 'Наземная станция',
            'router': 'Маршрутизатор',
            'core_router': 'Core Router',
            'switch': 'Коммутатор',
            'server': 'Сервер'
        };
        return names[type] || type;
    }
    
    setupEventListeners() {
        document.getElementById('btnExisting')?.addEventListener('click', () => {
            this.settings.showExisting = true;
            this.settings.showProposed = false;
            this.updateNetworkView();
            this.updateNetworkButtons('existing');
        });
        
        document.getElementById('btnProposed')?.addEventListener('click', () => {
            this.settings.showExisting = false;
            this.settings.showProposed = true;
            this.updateNetworkView();
            this.updateNetworkButtons('proposed');
        });
        
        document.getElementById('btnBoth')?.addEventListener('click', () => {
            this.settings.showExisting = true;
            this.settings.showProposed = true;
            this.updateNetworkView();
            this.updateNetworkButtons('both');
        });
        
        document.getElementById('btnRotate')?.addEventListener('click', () => {
            this.settings.isRotating = true;
            this.updateRotationButtons('rotate');
        });
        
        document.getElementById('btnStop')?.addEventListener('click', () => {
            this.settings.isRotating = false;
            this.updateRotationButtons('stop');
        });
        
        document.getElementById('chkSatellites')?.addEventListener('change', (e) => {
            this.settings.showSatellites = e.target.checked;
            this.updateNetworkView();
        });
        
        document.getElementById('chkStations')?.addEventListener('change', (e) => {
            this.settings.showStations = e.target.checked;
            this.updateNetworkView();
        });
        
        document.getElementById('chkRouters')?.addEventListener('change', (e) => {
            this.settings.showRouters = e.target.checked;
            this.updateNetworkView();
        });
        
        document.getElementById('chkCables')?.addEventListener('change', (e) => {
            this.settings.showCables = e.target.checked;
            this.updateNetworkView();
        });
        
        document.getElementById('chkProposed')?.addEventListener('change', (e) => {
            this.settings.showProposed = e.target.checked;
            this.updateNetworkView();
        });
        
        document.getElementById('zoomSlider')?.addEventListener('input', (e) => {
            this.settings.zoomLevel = parseInt(e.target.value);
            this.updateZoom();
        });
        
        window.addEventListener('resize', () => this.onWindowResize());
    }
    
    updateNetworkView() {
        this.clearNetworkElements();
        this.createNetworkElements();
        this.createCables();
        this.updateCounters();
    }
    
    updateNetworkButtons(type) {
        ['btnExisting', 'btnProposed', 'btnBoth'].forEach(id => {
            document.getElementById(id)?.classList.remove('active');
        });
        
        const btnMap = {
            'existing': 'btnExisting',
            'proposed': 'btnProposed',
            'both': 'btnBoth'
        };
        
        document.getElementById(btnMap[type])?.classList.add('active');
    }
    
    updateRotationButtons(type) {
        ['btnRotate', 'btnStop'].forEach(id => {
            document.getElementById(id)?.classList.remove('active');
        });
        
        document.getElementById(type === 'rotate' ? 'btnRotate' : 'btnStop')?.classList.add('active');
    }
    
    updateZoom() {
        if (!this.controls) return;
        
        const minDistance = 15;
        const maxDistance = 100;
        const zoomPercent = this.settings.zoomLevel / 100;
        const targetDistance = minDistance + (maxDistance - minDistance) * (1 - zoomPercent);
        
        this.camera.position.set(0, 0, targetDistance);
        this.controls.update();
    }
    
    updateCounters() {
        const elementCount = document.getElementById('elementCount');
        const connectionCount = document.getElementById('connectionCount');
        
        if (elementCount) {
            elementCount.textContent = this.equipment.length;
        }
        
        if (connectionCount) {
            connectionCount.textContent = this.connections.length + this.cableLines.length;
        }
    }
    
    onWindowResize() {
        const canvas = document.getElementById('globeCanvas');
        if (!canvas || !this.camera || !this.renderer) return;
        
        this.camera.aspect = canvas.clientWidth / canvas.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(canvas.clientWidth, canvas.clientHeight);
    }
    
    animate() {
        requestAnimationFrame(() => this.animate());
        
        if (this.settings.isRotating) {
            if (this.earth) this.earth.rotation.y += 0.001;
            if (this.clouds) this.clouds.rotation.y += 0.0015;
            
            this.satellites.forEach((satellite, index) => {
                const time = Date.now() * 0.001;
                const angle = time * 0.5 + index;
                const radius = 12 + Math.sin(time + index) * 0.5;
                
                satellite.position.x = Math.cos(angle) * radius;
                satellite.position.z = Math.sin(angle) * radius;
                satellite.position.y = Math.sin(time * 0.7 + index) * 2;
                
                satellite.rotation.x = time;
                satellite.rotation.y = time * 0.5;
            });
            
            this.equipment.forEach(item => {
                if (!item.userData.isSatellite && this.earth) {
                    const lat = item.userData.lat || 0;
                    const lng = item.userData.lng || 0;
                    const alt = item.userData.alt || 0;
                    
                    const rotatedLng = lng + (this.earth.rotation.y * 57.2958);
                    const newPos = this.latLngAltToVector3(lat, rotatedLng, alt);
                    
                    if (alt === 0) {
                        const surfacePos = newPos.clone().normalize().multiplyScalar(10.01);
                        item.position.copy(surfacePos);
                    } else {
                        item.position.copy(newPos);
                    }
                }
            });
        }
        
        if (this.controls) this.controls.update();
        if (this.renderer && this.scene && this.camera) {
            this.renderer.render(this.scene, this.camera);
        }
    }
}

let networkGlobe = null;

function initGlobe() {
    networkGlobe = new NetworkGlobe();
    window.Z96A = window.Z96A || {};
    window.Z96A.globe = networkGlobe;
}

function toggleNewsPanel() {
    const newsPanel = document.getElementById('newsPanel');
    if (newsPanel) {
        newsPanel.classList.toggle('open');
        
        const toggleBtn = newsPanel.querySelector('.panel-toggle i');
        if (toggleBtn) {
            toggleBtn.className = newsPanel.classList.contains('open') ? 
                'fas fa-chevron-right' : 'fas fa-chevron-left';
        }
    }
}
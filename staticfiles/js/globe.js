// 3D Визуализация сети на глобусе

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
	this.cableData = null;
        this.selectedElement = null;
        
        // Настройки
        this.settings = {
            showExisting: true,
	    showProposed: true,
            showProposed: true,
            showSatellites: true,
            showStations: true,
            showRouters: true,
            showCables: true,
            zoomLevel: 50,
            isRotating: true // Добавляем вращение
        };
        
        // Данные
        this.networkData = null;
        
        // Цвета
        this.colors = {
            earth: 0x1a5fb4,
            land: 0x26a269,
            existing: 0x6c63ff,
            proposed: 0x00ff9d,
            satellite: 0xf5f5f5,
            station: 0xffa348,
            router: 0xed333b,
            cable: 0x888888
        };
        
        this.init();
    }
    
    async init() {
        await this.loadNetworkData();
	await this.loadCableData();
        this.setupScene();
        this.createEarth();
        this.createNetworkElements();
        this.setupControls();
        this.setupEventListeners();
        this.animate();
        this.updateCounters();

	console.log('Cables loaded:', this.cableData?.cables?.length || 0);
    }
    
async loadCableData() {
    try {
        // ПРОБУЕМ ТАК
        const response = await fetch('/static/data/cables.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        this.cableData = await response.json();
        console.log('Cable data loaded:', this.cableData);
    } catch (error) {
        console.error('Error loading cable data:', error);
        // Создаем демо данные если файл не найден
        this.cableData = {
            cables: [
                {
                    id: 'test1',
                    name: 'Тестовый кабель',
                    type: 'submarine',
                    color: '#ff0000',
                    route: [
                        {lat: 40.7128, lng: -74.0060, name: 'Нью-Йорк'},
                        {lat: 51.5074, lng: -0.1278, name: 'Лондон'}
                    ]
                }
            ]
        };
    }
}
    
  async loadNetworkData() {
    try {
        const response = await fetch('/ru/api/network-data/');
        this.networkData = await response.json();
    } catch (error) {
        console.error('Error loading network data:', error);
        this.loadDemoData();
    }
}
    
    setupScene() {
        const canvas = document.getElementById('globeCanvas');
        if (!canvas) return;
        
        // Сцена
        this.scene = new THREE.Scene();
        this.scene.fog = new THREE.Fog(0x0a1a2d, 100, 1000);
        
        // Камера
        this.camera = new THREE.PerspectiveCamera(
            75,
            canvas.clientWidth / canvas.clientHeight,
            0.1,
            2000
        );
        this.camera.position.set(0, 0, 25);
        
        // Рендерер
        this.renderer = new THREE.WebGLRenderer({
            canvas,
            antialias: true,
            alpha: true
        });
        this.renderer.setSize(canvas.clientWidth, canvas.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.setClearColor(0x000000, 0);
        
        // Освещение
        const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
        this.scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 10, 5);
        this.scene.add(directionalLight);
        
        // Звездное небо
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
        
        // Текстура Земли
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
        
        // Облака
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
        
        const radius = 10 + (alt / 1000); // Масштабируем высоту
        
        return new THREE.Vector3(
            -radius * Math.sin(phi) * Math.cos(theta),
            radius * Math.cos(phi),
            radius * Math.sin(phi) * Math.sin(theta)
        );
    }
    
    createNetworkElements() {
        if (!this.networkData) return;
        
        // Очищаем старые элементы
        this.clearNetworkElements();
        
        // Создаем элементы
        this.networkData.elements.forEach(element => {
            if (!this.shouldShowElement(element)) return;
            
            const position = this.latLngAltToVector3(element.lat, element.lng, element.alt);
            const elementMesh = this.createElementMesh(element, position);
            
            if (elementMesh) {
                // ДЛЯ НАЗЕМНОГО ОБОРУДОВАНИЯ - ПРИВЯЗЫВАЕМ К ПОВЕРХНОСТИ
                if (element.type !== 'satellite') {
                    // Направляем оборудование "вверх" от поверхности
                    const upVector = position.clone().normalize();
                    
                    // Для станций и роутеров - ставим на поверхность
                    if (element.alt === 0) {
                        // Немного приподнимаем над поверхностью
                        const surfacePos = position.clone().normalize().multiplyScalar(10.01);
                        elementMesh.position.copy(surfacePos);
                    } else {
                        elementMesh.position.copy(position);
                    }
                } else {
                    // Для спутников - обычная позиция
                    elementMesh.position.copy(position);
                }
                
                this.scene.add(elementMesh);
                
                // Сохраняем ссылку на данные
                elementMesh.userData = { 
                    ...element, 
                    originalPosition: position.clone(),
                    isSatellite: element.type === 'satellite'
                };
                
                // Добавляем в общий массив
                this.equipment.push(elementMesh);
                
                // Для спутников отдельный массив
                if (element.type === 'satellite') {
                    this.satellites.push(elementMesh);
                }
            }
        });
        
        // Создаем соединения
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
                // Направляем конус вверх от поверхности
                geometry.rotateX(Math.PI);
                break;
                
            case 'router':
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
        
	/*
        // Добавляем свечение для предложенных элементов
        if (element.network === 'proposed') {
            const glowGeometry = new THREE.SphereGeometry(0.25, 16, 16);
            const glowMaterial = new THREE.MeshBasicMaterial({
                color: this.colors.proposed,
                transparent: true,
                opacity: 0.3
            });
            const glow = new THREE.Mesh(glowGeometry, glowMaterial);
            glow.position.copy(position);
            this.scene.add(glow);
            
            // Анимация пульсации
            this.animatePulsation(glow);
        }
        */
        return mesh;
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
                color = this.colors.cable;
        }
        
        const material = new THREE.LineBasicMaterial({
            color: color,
            transparent: true,
            opacity: 0.6,
            linewidth: 1
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
                return this.settings.showRouters;
            default:
                return true;
        }
    }
    
    shouldShowConnection(connection) {
        return this.settings.showCables;
    }
    
    clearNetworkElements() {
        // Удаляем все элементы и соединения
        this.equipment.forEach(mesh => {
            this.scene.remove(mesh);
        });
        
        this.connections.forEach(conn => {
            this.scene.remove(conn);
        });
        
        this.satellites = [];
        this.equipment = [];
        this.connections = [];
    }
    
    setupControls() {
        const canvas = document.getElementById('globeCanvas');
        if (!canvas || !this.camera || !this.renderer) return;
        
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.minDistance = 15;
        this.controls.maxDistance = 100;
        this.controls.maxPolarAngle = Math.PI;
        
        // Обработка кликов
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
            
            // Проверяем пересечение с элементами сети
            const intersects = raycaster.intersectObjects(this.equipment);
            
            if (intersects.length > 0) {
                const element = intersects[0].object;
                this.selectElement(element.userData);
            } else {
                // Проверяем пересечение с Землей
                const earthIntersects = raycaster.intersectObject(this.earth);
                if (earthIntersects.length > 0) {
                    this.selectEarthPoint(earthIntersects[0].point);
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
            
            // Подсветка при наведении
            this.equipment.forEach(el => {
                el.material.emissive.setHex(0x222222);
            });
            
            const intersects = raycaster.intersectObjects(this.equipment);
            
            if (intersects.length > 0) {
                const element = intersects[0].object;
                element.material.emissive.setHex(0x666666);
                canvas.style.cursor = 'pointer';
            } else {
                canvas.style.cursor = 'grab';
            }
        });
    }
    
    selectElement(elementData) {
        this.selectedElement = elementData;
        this.showElementInfo(elementData);
        
        // Подсветка выбранного элемента
        this.equipment.forEach(el => {
            if (el.userData.id === elementData.id) {
                el.material.emissive.setHex(0xffaa00);
            } else {
                el.material.emissive.setHex(0x222222);
            }
        });
    }
    
    selectEarthPoint(point) {
        // Преобразуем координаты точки в широту/долготу
        const lat = 90 - (Math.acos(point.y / point.length()) * 180 / Math.PI);
        const lng = (Math.atan2(point.z, point.x) * 180 / Math.PI);
        
        this.showEarthPointInfo(lat, lng);
    }
    
    clearSelection() {
        this.selectedElement = null;
        
        // Сбрасываем подсветку
        this.equipment.forEach(el => {
            el.material.emissive.setHex(0x222222);
        });
        
        this.clearElementInfo();
    }
    
    showElementInfo(elementData) {
        const infoPanel = document.getElementById('elementInfo');
        if (!infoPanel) return;
        
        let proposalsHtml = '';
        if (elementData.proposed_by) {
            proposalsHtml = `
                <div class="proposal-info">
                    <h4>Предложено:</h4>
                    <p>Пользователем: ${elementData.proposed_by}</p>
                    ${elementData.proposal_tx ? `
                        <p>Транзакция: 
                            <a href="https://solscan.io/tx/${elementData.proposal_tx}" target="_blank">
                                ${elementData.proposal_tx.slice(0, 20)}...
                            </a>
                        </p>
                    ` : ''}
                </div>
            `;
        }
        
        let specsHtml = '';
        if (elementData.specifications && Object.keys(elementData.specifications).length > 0) {
            specsHtml = `
                <h4>Характеристики:</h4>
                <ul>
                    ${Object.entries(elementData.specifications).map(([key, value]) => `
                        <li><strong>${key}:</strong> ${value}</li>
                    `).join('')}
                </ul>
            `;
        }
        
        infoPanel.innerHTML = `
            <h3>${elementData.name}</h3>
            <p><strong>Тип:</strong> ${this.getElementTypeName(elementData.type)}</p>
            <p><strong>Сеть:</strong> ${elementData.network === 'existing' ? 'Существующая' : 'Предложенная'}</p>
            <p><strong>Координаты:</strong> ${elementData.lat.toFixed(4)}°, ${elementData.lng.toFixed(4)}°</p>
            <p><strong>Высота:</strong> ${elementData.alt} км</p>
            <p>${elementData.description}</p>
            ${specsHtml}
            ${proposalsHtml}
            ${elementData.image_url ? `<img src="${elementData.image_url}" alt="${elementData.name}" style="max-width:100%; border-radius:4px; margin-top:10px;">` : ''}
        `;
    }
    
    showEarthPointInfo(lat, lng) {
        const infoPanel = document.getElementById('elementInfo');
        if (!infoPanel) return;
        
        infoPanel.innerHTML = `
            <h3>Точка на поверхности</h3>
            <p><strong>Широта:</strong> ${lat.toFixed(4)}°</p>
            <p><strong>Долгота:</strong> ${lng.toFixed(4)}°</p>
            <p>Кликните на элемент сети для получения подробной информации</p>
            <button class="add-element-btn" onclick="showAddElementModal(${lat.toFixed(4)}, ${lng.toFixed(4)})">
                <i class="fas fa-plus"></i> Добавить элемент здесь
            </button>
        `;
    }
    
    clearElementInfo() {
        const infoPanel = document.getElementById('elementInfo');
        if (infoPanel) {
            infoPanel.innerHTML = '<p>Выберите элемент сети для получения информации</p>';
        }
    }
    
    getElementTypeName(type) {
        const typeNames = {
            'satellite': 'Спутник',
            'ground_station': 'Наземная станция',
            'router': 'Маршрутизатор',
            'switch': 'Коммутатор',
            'server': 'Сервер',
            'cable': 'Кабельное соединение'
        };
        
        return typeNames[type] || type;
    }
    
    setupEventListeners() {
        // Кнопки переключения сети
        document.getElementById('btnExisting')?.addEventListener('click', (e) => {
            this.settings.showExisting = true;
            this.settings.showProposed = false;
            this.updateNetworkView();
            this.updateNetworkMode('Существующая');
            this.updateNetworkButtons('existing');
        });
        
        document.getElementById('btnProposed')?.addEventListener('click', (e) => {
            this.settings.showExisting = false;
            this.settings.showProposed = true;
            this.updateNetworkView();
            this.updateNetworkMode('Предложенная');
            this.updateNetworkButtons('proposed');
        });
        
        document.getElementById('btnBoth')?.addEventListener('click', (e) => {
            this.settings.showExisting = true;
            this.settings.showProposed = true;
            this.updateNetworkView();
            this.updateNetworkMode('Обе сети');
            this.updateNetworkButtons('both');
        });
        
        // Кнопки вращения
        document.getElementById('btnRotate')?.addEventListener('click', (e) => {
            this.settings.isRotating = true;
            this.updateRotationButtons('rotate');
        });
        
        document.getElementById('btnStop')?.addEventListener('click', (e) => {
            this.settings.isRotating = false;
            this.updateRotationButtons('stop');
        });
        
        // Чекбоксы элементов
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
        
        // Слайдер зума
        document.getElementById('zoomSlider')?.addEventListener('input', (e) => {
            this.settings.zoomLevel = parseInt(e.target.value);
            this.updateZoom();
        });
        // ДОБАВЛЯЕМ ОБРАБОТЧИК ДЛЯ ПРЕДЛОЖЕННЫХ ЭЛЕМЕНТОВ
        document.getElementById('chkProposed')?.addEventListener('change', (e) => {
            this.settings.showProposed = e.target.checked;
            this.updateNetworkView();
        });
        
        // Ресайз окна
        window.addEventListener('resize', () => this.onWindowResize());
    }
    
    updateNetworkView() {
        this.createNetworkElements();
        this.updateCounters();
    }
    
    updateNetworkMode(mode) {
        const modeElement = document.getElementById('networkMode');
        if (modeElement) {
            modeElement.textContent = mode;
        }
    }
    
    updateNetworkButtons(activeType) {
        const existingBtn = document.getElementById('btnExisting');
        const proposedBtn = document.getElementById('btnProposed');
        const bothBtn = document.getElementById('btnBoth');
        
        [existingBtn, proposedBtn, bothBtn].forEach(btn => {
            if (btn) btn.classList.remove('active');
        });
        
        if (activeType === 'existing' && existingBtn) {
            existingBtn.classList.add('active');
        } else if (activeType === 'proposed' && proposedBtn) {
            proposedBtn.classList.add('active');
        } else if (activeType === 'both' && bothBtn) {
            bothBtn.classList.add('active');
        }
    }
    
    updateRotationButtons(activeBtn) {
        const rotateBtn = document.getElementById('btnRotate');
        const stopBtn = document.getElementById('btnStop');
        
        if (rotateBtn && stopBtn) {
            rotateBtn.classList.remove('active');
            stopBtn.classList.remove('active');
            
            if (activeBtn === 'rotate') {
                rotateBtn.classList.add('active');
            } else {
                stopBtn.classList.add('active');
            }
        }
    }
    
    updateZoom() {
        if (this.controls) {
            const minDistance = 15;
            const maxDistance = 100;
            const zoomPercent = this.settings.zoomLevel / 100;
            const targetDistance = minDistance + (maxDistance - minDistance) * (1 - zoomPercent);
            
            // Плавное изменение зума
            this.controls.minDistance = targetDistance * 0.8;
            this.controls.maxDistance = targetDistance * 1.2;
            
            if (Math.abs(this.controls.getDistance() - targetDistance) > 1) {
                this.controls.target.set(0, 0, 0);
                this.camera.position.set(0, 0, targetDistance);
                this.controls.update();
            }
        }
    }
    
    updateCounters() {
        const elementCount = document.getElementById('elementCount');
        const connectionCount = document.getElementById('connectionCount');
        
        if (elementCount) {
            const visibleElements = this.networkData?.elements?.filter(el => 
                this.shouldShowElement(el)
            ).length || 0;
            elementCount.textContent = visibleElements;
        }
        
        if (connectionCount) {
            const visibleConnections = this.networkData?.connections?.filter(conn => 
                this.shouldShowConnection(conn)
            ).length || 0;
            connectionCount.textContent = visibleConnections;
        }
    }
    
    onWindowResize() {
        const canvas = document.getElementById('globeCanvas');
        if (!canvas || !this.camera || !this.renderer) return;
        
        this.camera.aspect = canvas.clientWidth / canvas.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(canvas.clientWidth, canvas.clientHeight);
    }
    
    animatePulsation(mesh) {
        let scale = 1;
        let direction = 0.01;
        
        const animate = () => {
            scale += direction;
            
            if (scale > 1.5) direction = -0.01;
            if (scale < 1) direction = 0.01;
            
            mesh.scale.set(scale, scale, scale);
            requestAnimationFrame(animate);
        };
        
        animate();
    }
    
    animate() {
        requestAnimationFrame(() => this.animate());
        
        // Вращение Земли - ТОЛЬКО ЕСЛИ ВКЛЮЧЕНО
        if (this.settings.isRotating) {
            if (this.earth) {
                this.earth.rotation.y += 0.001;
            }
            
            // Вращение облаков
            if (this.clouds) {
                this.clouds.rotation.y += 0.0015;
            }
            
            // Анимация спутников - ТОЛЬКО ЕСЛИ ВКЛЮЧЕНО
            this.satellites.forEach((satellite, index) => {
                if (satellite.userData.isSatellite) {
                    const time = Date.now() * 0.001;
                    const angle = time * 0.5 + index;
                    const radius = 12 + Math.sin(time + index) * 0.5;
                    
                    satellite.position.x = Math.cos(angle) * radius;
                    satellite.position.z = Math.sin(angle) * radius;
                    satellite.position.y = Math.sin(time * 0.7 + index) * 2;
                    
                    satellite.rotation.x = time;
                    satellite.rotation.y = time * 0.5;
                }
            });
            
            // Наземное оборудование ВРАЩАЕТСЯ ВМЕСТЕ С ЗЕМЛЁЙ
            this.equipment.forEach(item => {
                if (!item.userData.isSatellite && this.earth) {
                    // Обновляем позицию относительно вращающейся Земли
                    const lat = item.userData.lat || 0;
                    const lng = item.userData.lng || 0;
                    const alt = item.userData.alt || 0;
                    
                    // Добавляем вращение Земли к долготе
                    const rotatedLng = lng + (this.earth.rotation.y * 57.2958); // радианы в градусы
                    const newPos = this.latLngAltToVector3(lat, rotatedLng, alt);
                    
                    if (alt === 0) {
                        // Для наземного - на поверхности
                        const surfacePos = newPos.clone().normalize().multiplyScalar(10.01);
                        item.position.copy(surfacePos);
                    } else {
                        item.position.copy(newPos);
                    }
                }
            });
        }
        
        // Обновление контролов
        if (this.controls) {
            this.controls.update();
        }
        
        // Рендеринг
        if (this.renderer && this.scene && this.camera) {
            this.renderer.render(this.scene, this.camera);
        }
    }
}

// Глобальная функция для добавления элемента
function showAddElementModal(lat, lng) {
    const modal = document.getElementById('proposalModal');
    const locationInput = document.getElementById('proposalLocation');
    
    if (modal && locationInput) {
        locationInput.value = `${lat}, ${lng}`;
        modal.style.display = 'block';
    }
}

// Инициализация глобуса
let networkGlobe = null;

function initGlobe() {
    networkGlobe = new NetworkGlobe();
    window.Z96A.globe = networkGlobe;
}

// Переключение панели новостей
function toggleNewsPanel() {
    const newsPanel = document.getElementById('newsPanel');
    if (newsPanel) {
        newsPanel.classList.toggle('open');
        
        const toggleBtn = newsPanel.querySelector('.panel-toggle i');
        if (toggleBtn) {
            if (newsPanel.classList.contains('open')) {
                toggleBtn.className = 'fas fa-chevron-right';
            } else {
                toggleBtn.className = 'fas fa-chevron-left';
            }
        }
    }
}
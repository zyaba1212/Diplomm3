// Z96A 3D Globe with Three.js
class Z96AGlobe {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error('Globe container not found');
            return;
        }
        
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.globe = null;
        this.controls = null;
        this.nodes = [];
        this.connections = [];
        
        this.rotationSpeed = 0.001;
        this.isRotating = true;
        this.zoomLevel = 500;
        
        this.networkData = {
            existing: [],
            proposed: []
        };
        
        this.init();
    }
    
    async init() {
        try {
            // Загружаем Three.js если не загружен
            await this.loadThreeJS();
            
            // Настраиваем сцену
            this.setupScene();
            
            // Создаем глобус
            await this.createGlobe();
            
            // Добавляем освещение
            this.setupLighting();
            
            // Загружаем данные сети
            await this.loadNetworkData();
            
            // Добавляем элементы сети
            this.addNetworkElements();
            
            // Настраиваем контролы
            this.setupControls();
            
            // Запускаем анимацию
            this.animate();
            
            // Обработка ресайза
            this.setupResizeHandler();
            
            // Скрываем сообщение о загрузке
            this.hideLoading();
            
            console.log('3D Globe initialized successfully');
            
        } catch (error) {
            console.error('Error initializing 3D globe:', error);
            this.showFallback();
        }
    }
    
    async loadThreeJS() {
        if (typeof THREE !== 'undefined') {
            return;
        }
        
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://unpkg.com/three@0.155.0/build/three.min.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
    
    setupScene() {
        // Сцена
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0a0a1a);
        
        // Камера
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera = new THREE.PerspectiveCamera(45, width / height, 1, 2000);
        this.camera.position.z = this.zoomLevel;
        
        // Рендерер
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true, 
            alpha: true,
            powerPreference: "high-performance"
        });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        
        this.container.appendChild(this.renderer.domElement);
    }
    
    async createGlobe() {
        const radius = 200;
        
        // Загружаем текстуры Земли
        const textures = await this.loadEarthTextures();
        
        // Геометрия Земли
        const geometry = new THREE.SphereGeometry(radius, 128, 128);
        
        // Материал Земли
        const material = new THREE.MeshPhongMaterial({
            map: textures.color,
            bumpMap: textures.bump,
            bumpScale: 0.05,
            specularMap: textures.specular,
            specular: new THREE.Color(0x333333),
            shininess: 5
        });
        
        // Создаем Землю
        this.globe = new THREE.Mesh(geometry, material);
        this.scene.add(this.globe);
        
        // Добавляем атмосферу
        this.createAtmosphere(radius);
        
        // Добавляем звезды
        this.createStars();
        
        // Добавляем облака
        this.createClouds(radius);
    }
    
    async loadEarthTextures() {
        // Создаем текстуры программно для демонстрации
        const createTexture = (color, detail = false) => {
            const canvas = document.createElement('canvas');
            const size = detail ? 2048 : 1024;
            canvas.width = size * 2;
            canvas.height = size;
            const ctx = canvas.getContext('2d');
            
            // Основной цвет
            ctx.fillStyle = color;
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            if (detail) {
                // Добавляем детали для bump/specular карт
                ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
                
                // Континенты
                const continents = [
                    { x: 0.15, y: 0.3, w: 0.2, h: 0.4 },  // Америка
                    { x: 0.5, y: 0.3, w: 0.25, h: 0.4 },  // Европа/Африка
                    { x: 0.75, y: 0.25, w: 0.2, h: 0.5 }, // Азия/Австралия
                ];
                
                continents.forEach(cont => {
                    ctx.fillRect(
                        canvas.width * cont.x,
                        canvas.height * cont.y,
                        canvas.width * cont.w,
                        canvas.height * cont.h
                    );
                });
            }
            
            const texture = new THREE.CanvasTexture(canvas);
            texture.wrapS = THREE.RepeatWrapping;
            texture.wrapT = THREE.RepeatWrapping;
            return texture;
        };
        
        return {
            color: createTexture('#1a5fb4'),
            bump: createTexture('#888888', true),
            specular: createTexture('#000000', true)
        };
    }
    
    createAtmosphere(radius) {
        const atmosphereGeometry = new THREE.SphereGeometry(radius * 1.02, 64, 64);
        const atmosphereMaterial = new THREE.ShaderMaterial({
            uniforms: {
                glowColor: { value: new THREE.Color(0x0099ff) },
                viewVector: { value: this.camera.position }
            },
            vertexShader: `
                uniform vec3 viewVector;
                varying float intensity;
                void main() {
                    vec3 vNormal = normalize(normalMatrix * normal);
                    vec3 vNormel = normalize(normalMatrix * viewVector);
                    intensity = pow(0.8 - dot(vNormal, vNormel), 2.0);
                    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
                }
            `,
            fragmentShader: `
                uniform vec3 glowColor;
                varying float intensity;
                void main() {
                    vec3 glow = glowColor * intensity;
                    gl_FragColor = vec4(glow, intensity * 0.3);
                }
            `,
            side: THREE.BackSide,
            blending: THREE.AdditiveBlending,
            transparent: true
        });
        
        const atmosphere = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial);
        this.scene.add(atmosphere);
    }
    
    createStars() {
        const starGeometry = new THREE.BufferGeometry();
        const starCount = 10000;
        const positions = new Float32Array(starCount * 3);
        const colors = new Float32Array(starCount * 3);
        const sizes = new Float32Array(starCount);
        
        for (let i = 0; i < starCount; i++) {
            // Позиции в сфере
            const radius = 800 + Math.random() * 200;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos((Math.random() * 2) - 1);
            
            positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
            positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
            positions[i * 3 + 2] = radius * Math.cos(phi);
            
            // Цвета (белый с оттенками синего/фиолетового)
            colors[i * 3] = 0.8 + Math.random() * 0.2;     // R
            colors[i * 3 + 1] = 0.8 + Math.random() * 0.2; // G
            colors[i * 3 + 2] = 1.0;                       // B
            
            // Размеры
            sizes[i] = Math.random() * 2 + 0.5;
        }
        
        starGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        starGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        starGeometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
        
        const starMaterial = new THREE.PointsMaterial({
            size: 1,
            vertexColors: true,
            sizeAttenuation: true,
            transparent: true
        });
        
        const stars = new THREE.Points(starGeometry, starMaterial);
        this.scene.add(stars);
    }
    
    createClouds(radius) {
        const cloudGeometry = new THREE.SphereGeometry(radius * 1.01, 64, 64);
        
        // Создаем текстуру облаков
        const canvas = document.createElement('canvas');
        canvas.width = 1024;
        canvas.height = 512;
        const ctx = canvas.getContext('2d');
        
        // Прозрачный фон
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Рисуем облачные паттерны
        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        for (let i = 0; i < 50; i++) {
            const x = Math.random() * canvas.width;
            const y = Math.random() * canvas.height;
            const size = 20 + Math.random() * 80;
            
            ctx.beginPath();
            ctx.arc(x, y, size, 0, Math.PI * 2);
            ctx.fill();
        }
        
        const cloudTexture = new THREE.CanvasTexture(canvas);
        const cloudMaterial = new THREE.MeshLambertMaterial({
            map: cloudTexture,
            transparent: true,
            opacity: 0.4,
            side: THREE.DoubleSide
        });
        
        const clouds = new THREE.Mesh(cloudGeometry, cloudMaterial);
        clouds.rotation.y = Math.PI / 8;
        this.scene.add(clouds);
        
        // Анимация облаков
        this.clouds = clouds;
    }
    
    async loadNetworkData() {
        try {
            // Загружаем данные сети с сервера
            const response = await fetch('/api/network/nodes');
            const nodes = await response.json();
            
            // Разделяем на существующую и предлагаемую сети
            this.networkData.existing = nodes.filter(node => node.network_type === 'existing');
            this.networkData.proposed = nodes.filter(node => node.network_type === 'proposed');
            
        } catch (error) {
            console.error('Error loading network data:', error);
            
            // Используем демо данные
            this.networkData.existing = this.createDemoData('existing');
            this.networkData.proposed = this.createDemoData('proposed');
        }
    }
    
    createDemoData(type) {
        const data = [];
        const colors = type === 'existing' ? 0x0099ff : 0x9d4edd;
        
        // Ключевые города мира
        const cities = [
            { name: 'New York', lat: 40.7128, lon: -74.0060 },
            { name: 'London', lat: 51.5074, lon: -0.1278 },
            { name: 'Tokyo', lat: 35.6762, lon: 139.6503 },
            { name: 'Moscow', lat: 55.7558, lon: 37.6173 },
            { name: 'Singapore', lat: 1.3521, lon: 103.8198 },
            { name: 'Sydney', lat: -33.8688, lon: 151.2093 },
            { name: 'Frankfurt', lat: 50.1109, lon: 8.6821 },
            { name: 'São Paulo', lat: -23.5505, lon: -46.6333 },
            { name: 'Mumbai', lat: 19.0760, lon: 72.8777 },
            { name: 'Dubai', lat: 25.2048, lon: 55.2708 }
        ];
        
        cities.forEach(city => {
            data.push({
                id: `demo_${type}_${city.name}`,
                name: city.name,
                latitude: city.lat,
                longitude: city.lon,
                network_type: type,
                node_type: type === 'existing' ? 'data_center' : 'satellite',
                description: `${type === 'existing' ? 'Existing' : 'Proposed'} network node in ${city.name}`,
                capacity_gbps: type === 'existing' ? 100 : 50
            });
        });
        
        return data;
    }
    
    addNetworkElements() {
        // Добавляем узлы существующей сети
        this.networkData.existing.forEach(node => {
            this.addNode(node, 0x0099ff, 5);
        });
        
        // Добавляем узлы предлагаемой сети
        this.networkData.proposed.forEach(node => {
            this.addNode(node, 0x9d4edd, 4);
        });
        
        // Добавляем соединения
        this.addConnections();
    }
    
    addNode(nodeData, color, size) {
        const { latitude, longitude } = nodeData;
        
        // Конвертируем координаты
        const phi = (90 - latitude) * (Math.PI / 180);
        const theta = (longitude + 180) * (Math.PI / 180);
        const radius = 205; // Немного выше поверхности
        
        const x = -(radius * Math.sin(phi) * Math.cos(theta));
        const y = radius * Math.cos(phi);
        const z = radius * Math.sin(phi) * Math.sin(theta);
        
        // Создаем узел
        const geometry = new THREE.SphereGeometry(size, 16, 16);
        const material = new THREE.MeshBasicMaterial({ color });
        const node = new THREE.Mesh(geometry, material);
        node.position.set(x, y, z);
        
        // Сохраняем данные узла
        node.userData = nodeData;
        
        // Добавляем свечение
        const glowGeometry = new THREE.SphereGeometry(size * 1.5, 16, 16);
        const glowMaterial = new THREE.MeshBasicMaterial({
            color,
            transparent: true,
            opacity: 0.3
        });
        const glow = new THREE.Mesh(glowGeometry, glowMaterial);
        glow.position.set(x, y, z);
        glow.userData = { ...nodeData, isGlow: true };
        
        this.scene.add(node);
        this.scene.add(glow);
        
        this.nodes.push(node);
        this.nodes.push(glow);
        
        // Добавляем пульсацию
        this.addPulseAnimation(glow);
        
        return node;
    }
    
    addConnections() {
        // Создаем соединения между основными узлами
        const connections = [
            { from: 'New York', to: 'London', type: 'submarine', color: 0x00ff88 },
            { from: 'London', to: 'Frankfurt', type: 'terrestrial', color: 0x0099ff },
            { from: 'Tokyo', to: 'Singapore', type: 'submarine', color: 0x00ff88 },
            { from: 'New York', to: 'São Paulo', type: 'submarine', color: 0x00ff88 },
            { from: 'Dubai', to: 'Mumbai', type: 'terrestrial', color: 0x0099ff },
            { from: 'Sydney', to: 'Singapore', type: 'satellite', color: 0xff9900 }
        ];
        
        connections.forEach(conn => {
            this.addConnection(conn);
        });
    }
    
    addConnection(connection) {
        // Находим узлы
        const fromNode = this.findNodeByName(connection.from);
        const toNode = this.findNodeByName(connection.to);
        
        if (!fromNode || !toNode) return;
        
        // Создаем кривую для соединения
        const curve = new THREE.CatmullRomCurve3([
            fromNode.position,
            this.getMidpoint(fromNode.position, toNode.position, 50),
            toNode.position
        ]);
        
        // Создаем геометрию линии
        const points = curve.getPoints(50);
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        
        // Материал в зависимости от типа соединения
        let material;
        if (connection.type === 'submarine') {
            material = new THREE.LineDashedMaterial({
                color: connection.color,
                dashSize: 3,
                gapSize: 1,
                linewidth: 2
            });
        } else {
            material = new THREE.LineBasicMaterial({
                color: connection.color,
                linewidth: connection.type === 'satellite' ? 1 : 2,
                transparent: connection.type === 'satellite',
                opacity: connection.type === 'satellite' ? 0.6 : 1
            });
        }
        
        const line = new THREE.Line(geometry, material);
        if (connection.type === 'submarine') {
            line.computeLineDistances();
        }
        
        this.scene.add(line);
        this.connections.push(line);
        
        // Добавляем анимацию потока данных для спутниковых соединений
        if (connection.type === 'satellite') {
            this.addDataFlow(curve, connection.color);
        }
    }
    
    findNodeByName(name) {
        return this.nodes.find(node => 
            node.userData && node.userData.name === name && !node.userData.isGlow
        );
    }
    
    getMidpoint(p1, p2, height) {
        const midpoint = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
        midpoint.normalize().multiplyScalar(205 + height);
        return midpoint;
    }
    
    addDataFlow(curve, color) {
        // Создаем сферу для анимации потока данных
        const geometry = new THREE.SphereGeometry(1, 8, 8);
        const material = new THREE.MeshBasicMaterial({ color });
        const sphere = new THREE.Mesh(geometry, material);
        
        sphere.userData = {
            curve: curve,
            progress: Math.random(),
            speed: 0.002 + Math.random() * 0.003
        };
        
        this.scene.add(sphere);
        this.connections.push(sphere);
    }
    
    addPulseAnimation(glow) {
        glow.userData.pulse = {
            scale: 1,
            direction: 1,
            speed: 0.01
        };
    }
    
    setupLighting() {
        // Окружающий свет
        const ambientLight = new THREE.AmbientLight(0x404040);
        this.scene.add(ambientLight);
        
        // Направленный свет (солнце)
        const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
        directionalLight.position.set(5, 3, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        this.scene.add(directionalLight);
        
        // Точечный свет для эффектов
        const pointLight = new THREE.PointLight(0x0099ff, 0.5, 1000);
        pointLight.position.set(0, 0, 0);
        this.scene.add(pointLight);
    }
    
    setupControls() {
        // Raycaster для взаимодействия
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        
        // Обработка кликов
        this.container.addEventListener('click', (e) => this.onMouseClick(e));
        
        // Обработка перемещения мыши
        this.container.addEventListener('mousemove', (e) => this.onMouseMove(e));
        
        // Обработка колесика мыши
        this.container.addEventListener('wheel', (e) => this.onMouseWheel(e));
    }
    
    setupResizeHandler() {
        window.addEventListener('resize', () => {
            const width = this.container.clientWidth;
            const height = this.container.clientHeight;
            
            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(width, height);
        });
    }
    
    onMouseMove(event) {
        const rect = this.container.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        
        this.raycaster.setFromCamera(this.mouse, this.camera);
        
        // Находим пересечения
        const intersects = this.raycaster.intersectObjects(this.nodes);
        
        // Сбрасываем подсветку всех узлов
        this.nodes.forEach(node => {
            if (node.scale.x > 1) {
                node.scale.set(1, 1, 1);
            }
        });
        
        // Подсвечиваем узел под курсором
        if (intersects.length > 0) {
            const node = intersects[0].object;
            node.scale.set(1.3, 1.3, 1.3);
            
            // Показываем подсказку
            this.showTooltip(node.userData, event.clientX, event.clientY);
        } else {
            this.hideTooltip();
        }
    }
    
    onMouseClick(event) {
        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(this.nodes);
        
        if (intersects.length > 0) {
            const node = intersects[0].object;
            if (node.userData && !node.userData.isGlow) {
                this.showNodeDetails(node.userData);
            }
        }
    }
    
    onMouseWheel(event) {
        event.preventDefault();
        
        const delta = event.deltaY * 0.01;
        this.zoomLevel = THREE.MathUtils.clamp(this.zoomLevel + delta, 250, 1000);
        
        this.camera.position.z = this.zoomLevel;
    }
    
    showTooltip(nodeData, x, y) {
        let tooltip = document.getElementById('globe-tooltip');
        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.id = 'globe-tooltip';
            tooltip.style.cssText = `
                position: fixed;
                background: rgba(30, 30, 46, 0.95);
                border: 1px solid #9d4edd;
                border-radius: 8px;
                padding: 12px 15px;
                color: white;
                z-index: 10000;
                pointer-events: none;
                backdrop-filter: blur(5px);
                max-width: 300px;
                font-size: 0.9rem;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            `;
            document.body.appendChild(tooltip);
        }
        
        tooltip.innerHTML = `
            <div style="font-weight: bold; color: #00d4ff; margin-bottom: 5px;">${nodeData.name}</div>
            <div style="font-size: 0.8rem; color: #aaa; margin-bottom: 3px;">
                ${nodeData.node_type || 'Network Node'}
            </div>
            <div style="font-size: 0.8rem;">
                <span style="color: #9d4edd;">${nodeData.network_type === 'existing' ? '🌐 Existing' : '🚀 Proposed'}</span>
                <span style="margin: 0 10px;">•</span>
                <span>${nodeData.capacity_gbps || '0'} Gbps</span>
            </div>
        `;
        
        tooltip.style.left = (x + 15) + 'px';
        tooltip.style.top = (y + 15) + 'px';
        tooltip.style.display = 'block';
    }
    
    hideTooltip() {
        const tooltip = document.getElementById('globe-tooltip');
        if (tooltip) {
            tooltip.style.display = 'none';
        }
    }
    
    showNodeDetails(nodeData) {
        // Показываем модальное окно с деталями узла
        if (typeof window.showNodeDetails === 'function') {
            window.showNodeDetails(nodeData);
        }
    }
    
    animate() {
        requestAnimationFrame(() => this.animate());
        
        // Вращение глобуса
        if (this.isRotating && this.globe) {
            this.globe.rotation.y += this.rotationSpeed;
        }
        
        // Вращение облаков
        if (this.clouds) {
            this.clouds.rotation.y += this.rotationSpeed * 0.5;
        }
        
        // Анимация пульсации узлов
        this.nodes.forEach(node => {
            if (node.userData && node.userData.pulse) {
                const { pulse } = node.userData;
                pulse.scale += pulse.direction * pulse.speed;
                
                if (pulse.scale > 1.5) pulse.direction = -1;
                if (pulse.scale < 0.8) pulse.direction = 1;
                
                node.scale.set(pulse.scale, pulse.scale, pulse.scale);
            }
        });
        
        // Анимация потока данных
        this.connections.forEach(obj => {
            if (obj.userData && obj.userData.curve) {
                const { curve, progress, speed } = obj.userData;
                obj.userData.progress = (progress + speed) % 1;
                
                const point = curve.getPointAt(obj.userData.progress);
                obj.position.copy(point);
            }
        });
        
        // Рендеринг
        this.renderer.render(this.scene, this.camera);
    }
    
    hideLoading() {
        const loading = this.container.querySelector('.globe-loading');
        if (loading) {
            loading.style.opacity = '0';
            setTimeout(() => {
                loading.style.display = 'none';
            }, 300);
        }
    }
    
    showFallback() {
        const loading = this.container.querySelector('.globe-loading');
        if (loading) {
            loading.innerHTML = `
                <div style="text-align: center; padding: 40px;">
                    <div style="font-size: 48px; color: #ff9900; margin-bottom: 20px;">🌍</div>
                    <h3 style="color: var(--color-neon-blue); margin-bottom: 15px;">3D Network Globe</h3>
                    <p style="color: var(--color-text); margin-bottom: 30px;">
                        Advanced visualization of global network infrastructure
                    </p>
                    <div style="background: rgba(0,0,0,0.3); border-radius: 10px; padding: 20px; max-width: 400px; margin: 0 auto;">
                        <h4 style="color: var(--color-neon-purple); margin-bottom: 15px;">🎮 Interactive Features:</h4>
                        <ul style="text-align: left; padding-left: 20px;">
                            <li><strong>Drag:</strong> Rotate the globe</li>
                            <li><strong>Scroll:</strong> Zoom in/out</li>
                            <li><strong>Click nodes:</strong> View details</li>
                            <li><strong>Hover:</strong> See node information</li>
                        </ul>
                        <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--color-border);">
                            <p><span style="color: #0099ff;">●</span> Existing Network</p>
                            <p><span style="color: #9d4edd;">●</span> Proposed Network</p>
                            <p><span style="color: #00ff88;">●</span> Submarine Cables</p>
                            <p><span style="color: #ff9900;">●</span> Satellite Links</p>
                        </div>
                    </div>
                </div>
            `;
        }
    }
    
    // Публичные методы для управления глобусом
    setRotation(enabled) {
        this.isRotating = enabled;
    }
    
    setRotationSpeed(speed) {
        this.rotationSpeed = speed;
    }
    
    resetView() {
        this.camera.position.set(0, 0, 500);
        this.camera.lookAt(0, 0, 0);
        this.zoomLevel = 500;
    }
    
    toggleNetworkType(type) {
        // Показываем/скрываем узлы в зависимости от типа сети
        this.nodes.forEach(node => {
            if (node.userData && !node.userData.isGlow) {
                const showNode = 
                    type === 'hybrid' ||
                    node.userData.network_type === type;
                
                node.visible = showNode;
                
                // Также скрываем/показываем свечение
                const glow = this.nodes.find(n => 
                    n.userData && 
                    n.userData.isGlow && 
                    n.userData.id === node.userData.id
                );
                if (glow) glow.visible = showNode;
            }
        });
    }
    
    toggleLayer(layer, visible) {
        // Управление видимостью слоев
        switch(layer) {
            case 'submarine':
                this.connections.forEach(conn => {
                    if (conn.material.color.getHex() === 0x00ff88) {
                        conn.visible = visible;
                    }
                });
                break;
            case 'terrestrial':
                this.connections.forEach(conn => {
                    if (conn.material.color.getHex() === 0x0099ff && 
                        !conn.userData?.curve) {
                        conn.visible = visible;
                    }
                });
                break;
            case 'satellite':
                this.connections.forEach(conn => {
                    if (conn.material.color.getHex() === 0xff9900) {
                        conn.visible = visible;
                    }
                });
                break;
            case 'nodes':
                this.nodes.forEach(node => {
                    if (!node.userData?.isGlow) {
                        node.visible = visible;
                    }
                });
                break;
        }
    }
}

// Инициализация глобуса при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    window.Z96AGlobe = new Z96AGlobe('globe-container');
});
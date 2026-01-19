/**
 * Z96A - 3D Глобус с визуализацией сети
 * Версия: 1.0.0
 * Использует Three.js для 3D графики
 */

class GlobeScene {
    constructor(canvas, container) {
        this.canvas = canvas;
        this.container = container;
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        
        // Настройки
        this.settings = {
            autoRotate: true,
            showAtmosphere: true,
            showGrid: false,
            showStars: true,
            connectionOpacity: 0.7,
            elementSize: 1.0,
            animationSpeed: 1.0
        };
        
        // Данные
        this.networkElements = [];
        this.networkConnections = [];
        this.selectedElement = null;
        
        // Состояние
        this.isInitialized = false;
        this.animationId = null;
        
        // Цвета для типов соединений
        this.connectionColors = {
            'FIBER': 0x22c55e,    // Зеленый
            'SATELLITE': 0x3b82f6, // Синий
            'RADIO': 0xf59e0b,     // Оранжевый
            'BLUETOOTH': 0x8b5cf6, // Фиолетовый
            'CELLULAR': 0xec4899   // Розовый
        };
        
        // Цвета для типов сети
        this.networkTypeColors = {
            'EXISTING': 0x22c55e,  // Зеленый
            'PROPOSED': 0x3b82f6,  // Синий
            'HYBRID': 0x8b5cf6     // Фиолетовый
        };
        
        this.init();
    }
    
    init() {
        try {
            // Проверка поддержки WebGL
            if (!this.checkWebGLSupport()) {
                this.showWebGLError();
                return;
            }
            
            // Создание сцены
            this.scene = new THREE.Scene();
            this.scene.background = new THREE.Color(0x0f172a);
            
            // Создание камеры
            const width = this.container.clientWidth;
            const height = this.container.clientHeight;
            this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
            this.camera.position.set(0, 0, 300);
            
            // Создание рендерера
            this.renderer = new THREE.WebGLRenderer({
                canvas: this.canvas,
                antialias: true,
                alpha: true
            });
            this.renderer.setSize(width, height);
            this.renderer.setPixelRatio(window.devicePixelRatio);
            this.renderer.shadowMap.enabled = true;
            this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            
            // Добавление освещения
            this.setupLighting();
            
            // Создание Земли
            this.createEarth();
            
            // Добавление звездного фона
            if (this.settings.showStars) {
                this.createStarfield();
            }
            
            // Добавление атмосферы
            if (this.settings.showAtmosphere) {
                this.createAtmosphere();
            }
            
            // Добавление сетки координат
            if (this.settings.showGrid) {
                this.createGrid();
            }
            
            // Настройка управления
            this.setupControls();
            
            // Обработка изменения размера
            window.addEventListener('resize', () => this.onWindowResize());
            
            // Обработка кликов
            this.canvas.addEventListener('click', (event) => this.onCanvasClick(event));
            
            // Старт анимации
            this.animate();
            
            this.isInitialized = true;
            console.log('Globe scene initialized');
            
        } catch (error) {
            console.error('Error initializing globe:', error);
            this.showInitializationError();
        }
    }
    
    checkWebGLSupport() {
        try {
            const canvas = document.createElement('canvas');
            return !!(window.WebGLRenderingContext && 
                     (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
        } catch (e) {
            return false;
        }
    }
    
    showWebGLError() {
        this.container.innerHTML = `
            <div style="text-align: center; padding: 4rem; color: #ef4444;">
                <h3 style="margin-bottom: 1rem;">WebGL не поддерживается</h3>
                <p style="color: #94a3b8; margin-bottom: 1.5rem;">
                    Ваш браузер не поддерживает WebGL, необходимый для 3D визуализации.
                </p>
                <div style="display: flex; gap: 1rem; justify-content: center;">
                    <button onclick="location.reload()" style="padding: 0.75rem 1.5rem; background: #3b82f6; color: white; border: none; border-radius: 8px; cursor: pointer;">
                        Обновить страницу
                    </button>
                    <a href="https://get.webgl.org/" target="_blank" style="padding: 0.75rem 1.5rem; background: transparent; color: #6ee7ff; border: 1px solid #6ee7ff; border-radius: 8px; text-decoration: none;">
                        Узнать больше
                    </a>
                </div>
            </div>
        `;
    }
    
    showInitializationError() {
        this.container.innerHTML = `
            <div style="text-align: center; padding: 4rem; color: #ef4444;">
                <h3 style="margin-bottom: 1rem;">Ошибка инициализации 3D сцены</h3>
                <p style="color: #94a3b8; margin-bottom: 1.5rem;">
                    Не удалось загрузить 3D визуализацию. Пожалуйста, попробуйте обновить страницу.
                </p>
                <button onclick="location.reload()" style="padding: 0.75rem 1.5rem; background: #3b82f6; color: white; border: none; border-radius: 8px; cursor: pointer;">
                    Обновить страницу
                </button>
            </div>
        `;
    }
    
    setupLighting() {
        // Основной свет
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        this.scene.add(ambientLight);
        
        // Направленный свет (солнце)
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(100, 100, 50);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        this.scene.add(directionalLight);
        
        // Заполняющий свет
        const fillLight = new THREE.DirectionalLight(0x6ee7ff, 0.3);
        fillLight.position.set(-100, -100, -50);
        this.scene.add(fillLight);
    }
    
    createEarth() {
        // Геосфера (Земля)
        const earthGeometry = new THREE.SphereGeometry(100, 64, 64);
        
        // Текстура Земли
        const earthTexture = new THREE.TextureLoader().load(
            'https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/planets/earth_atmos_2048.jpg',
            () => {
                console.log('Earth texture loaded');
            },
            undefined,
            (error) => {
                console.error('Error loading earth texture:', error);
            }
        );
        
        const earthMaterial = new THREE.MeshPhongMaterial({
            map: earthTexture,
            bumpScale: 0.05,
            specular: new THREE.Color(0x333333),
            shininess: 5
        });
        
        this.earth = new THREE.Mesh(earthGeometry, earthMaterial);
        this.earth.rotation.y = -Math.PI / 2;
        this.scene.add(this.earth);
        
        // Облака
        const cloudGeometry = new THREE.SphereGeometry(101, 64, 64);
        const cloudMaterial = new THREE.MeshPhongMaterial({
            map: new THREE.TextureLoader().load('https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/planets/earth_clouds_1024.png'),
            transparent: true,
            opacity: 0.4
        });
        
        this.clouds = new THREE.Mesh(cloudGeometry, cloudMaterial);
        this.scene.add(this.clouds);
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
            size: 1.5,
            transparent: true
        });
        
        const stars = new THREE.Points(starGeometry, starMaterial);
        this.scene.add(stars);
    }
    
    createAtmosphere() {
        const atmosphereGeometry = new THREE.SphereGeometry(103, 64, 64);
        const atmosphereMaterial = new THREE.ShaderMaterial({
            uniforms: {
                glowColor: { value: new THREE.Color(0x6ee7ff) },
                viewVector: { value: this.camera.position }
            },
            vertexShader: `
                uniform vec3 viewVector;
                varying float intensity;
                void main() {
                    vec3 vNormal = normalize(normalMatrix * normal);
                    vec3 vNormel = normalize(normalMatrix * viewVector);
                    intensity = pow(0.7 - dot(vNormal, vNormel), 2.0);
                    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
                }
            `,
            fragmentShader: `
                uniform vec3 glowColor;
                varying float intensity;
                void main() {
                    vec3 glow = glowColor * intensity;
                    gl_FragColor = vec4(glow, 1.0);
                }
            `,
            side: THREE.BackSide,
            blending: THREE.AdditiveBlending,
            transparent: true
        });
        
        this.atmosphere = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial);
        this.scene.add(this.atmosphere);
    }
    
    createGrid() {
        const gridHelper = new THREE.GridHelper(300, 30, 0x444444, 0x222222);
        gridHelper.position.y = -150;
        this.scene.add(gridHelper);
    }
    
    setupControls() {
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.rotateSpeed = 0.5;
        this.controls.zoomSpeed = 1.0;
        this.controls.panSpeed = 0.5;
        this.controls.minDistance = 150;
        this.controls.maxDistance = 500;
        this.controls.maxPolarAngle = Math.PI;
        this.controls.minPolarAngle = 0;
        this.controls.autoRotate = this.settings.autoRotate;
        this.controls.autoRotateSpeed = 0.5;
    }
    
    loadNetworkData(networkData) {
        if (!this.isInitialized) {
            console.error('Globe not initialized');
            return;
        }
        
        // Очистка предыдущих элементов
        this.clearNetworkElements();
        
        // Сохранение данных
        this.networkElements = networkData.elements || [];
        this.networkConnections = networkData.connections || [];
        
        // Создание элементов сети
        this.createNetworkElements();
        
        // Создание соединений
        this.createNetworkConnections();
        
        console.log(`Loaded ${this.networkElements.length} elements and ${this.networkConnections.length} connections`);
    }
    
    createNetworkElements() {
        this.networkElements.forEach((element, index) => {
            const element3D = this.createNetworkElement3D(element, index);
            this.scene.add(element3D.object3d);
            element.object3d = element3D.object3d;
            element.userData = element3D.userData;
        });
    }
    
    createNetworkElement3D(element, id) {
        const { latitude, longitude, altitude } = element;
        
        // Конвертация географических координат в 3D координаты
        const phi = (90 - latitude) * (Math.PI / 180);
        const theta = (longitude + 180) * (Math.PI / 180);
        
        const radius = 100 + (altitude || 0);
        const x = -(radius * Math.sin(phi) * Math.cos(theta));
        const y = radius * Math.cos(phi);
        const z = radius * Math.sin(phi) * Math.sin(theta);
        
        // Создание 3D объекта в зависимости от типа элемента
        let object3d;
        let color;
        
        switch (element.type) {
            case 'SATELLITE':
                color = 0x3b82f6; // Синий
                object3d = this.createSatellite(x, y, z, color);
                break;
            case 'GROUND_STATION':
                color = 0x22c55e; // Зеленый
                object3d = this.createGroundStation(x, y, z, color);
                break;
            case 'ROUTER':
                color = 0xf59e0b; // Оранжевый
                object3d = this.createRouter(x, y, z, color);
                break;
            default:
                color = 0x6ee7ff; // Голубой (по умолчанию)
                object3d = this.createGenericElement(x, y, z, color);
        }
        
        // Добавление пользовательских данных
        const userData = {
            id: id,
            elementId: element.id,
            type: element.type,
            name: element.name,
            description: element.description,
            coordinates: [longitude, latitude, altitude],
            originalData: element
        };
        
        object3d.userData = userData;
        
        return { object3d, userData };
    }
    
    createSatellite(x, y, z, color) {
        const group = new THREE.Group();
        group.position.set(x, y, z);
        
        // Основной корпус
        const geometry = new THREE.OctahedronGeometry(3, 0);
        const material = new THREE.MeshPhongMaterial({
            color: color,
            emissive: color,
            emissiveIntensity: 0.3,
            shininess: 100
        });
        const satellite = new THREE.Mesh(geometry, material);
        group.add(satellite);
        
        // Солнечные панели
        const panelGeometry = new THREE.BoxGeometry(8, 0.5, 4);
        const panelMaterial = new THREE.MeshPhongMaterial({
            color: 0xfbbf24,
            emissive: 0xfbbf24,
            emissiveIntensity: 0.2
        });
        
        const leftPanel = new THREE.Mesh(panelGeometry, panelMaterial);
        leftPanel.position.x = -6;
        group.add(leftPanel);
        
        const rightPanel = new THREE.Mesh(panelGeometry, panelMaterial);
        rightPanel.position.x = 6;
        group.add(rightPanel);
        
        // Антенна
        const antennaGeometry = new THREE.ConeGeometry(0.5, 4, 8);
        const antennaMaterial = new THREE.MeshPhongMaterial({ color: 0x94a3b8 });
        const antenna = new THREE.Mesh(antennaGeometry, antennaMaterial);
        antenna.position.y = 4;
        antenna.rotation.x = Math.PI;
        group.add(antenna);
        
        // Свечение
        const glowGeometry = new THREE.SphereGeometry(5, 16, 16);
        const glowMaterial = new THREE.MeshBasicMaterial({
            color: color,
            transparent: true,
            opacity: 0.2
        });
        const glow = new THREE.Mesh(glowGeometry, glowMaterial);
        group.add(glow);
        
        return group;
    }
    
    createGroundStation(x, y, z, color) {
        const group = new THREE.Group();
        group.position.set(x, y, z);
        
        // Основное здание
        const buildingGeometry = new THREE.CylinderGeometry(2, 3, 6, 8);
        const buildingMaterial = new THREE.MeshPhongMaterial({ color: color });
        const building = new THREE.Mesh(buildingGeometry, buildingMaterial);
        building.position.y = 3;
        group.add(building);
        
        // Антенна
        const dishGeometry = new THREE.CircleGeometry(5, 16);
        const dishMaterial = new THREE.MeshPhongMaterial({
            color: 0x94a3b8,
            side: THREE.DoubleSide
        });
        const dish = new THREE.Mesh(dishGeometry, dishMaterial);
        dish.position.y = 8;
        dish.rotation.x = Math.PI / 2;
        group.add(dish);
        
        // Опоры антенны
        const supportGeometry = new THREE.CylinderGeometry(0.2, 0.2, 2);
        const supportMaterial = new THREE.MeshPhongMaterial({ color: 0x64748b });
        
        for (let i = 0; i < 3; i++) {
            const angle = (i * Math.PI * 2) / 3;
            const support = new THREE.Mesh(supportGeometry, supportMaterial);
            support.position.set(
                Math.cos(angle) * 4,
                7,
                Math.sin(angle) * 4
            );
            group.add(support);
        }
        
        // Освещение
        const lightGeometry = new THREE.SphereGeometry(0.5, 8, 8);
        const lightMaterial = new THREE.MeshBasicMaterial({
            color: 0xffffff,
            emissive: 0xffffff,
            emissiveIntensity: 0.5
        });
        const light = new THREE.Mesh(lightGeometry, lightMaterial);
        light.position.y = 9;
        group.add(light);
        
        return group;
    }
    
    createRouter(x, y, z, color) {
        const group = new THREE.Group();
        group.position.set(x, y, z);
        
        // Корпус
        const bodyGeometry = new THREE.BoxGeometry(4, 2, 3);
        const bodyMaterial = new THREE.MeshPhongMaterial({ color: color });
        const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
        group.add(body);
        
        // Порты (светодиоды)
        const portGeometry = new THREE.SphereGeometry(0.3, 8, 8);
        const portMaterial = new THREE.MeshBasicMaterial({
            color: 0x22c55e,
            emissive: 0x22c55e,
            emissiveIntensity: 0.5
        });
        
        for (let i = 0; i < 8; i++) {
            const port = new THREE.Mesh(portGeometry, portMaterial);
            port.position.set(
                -1.5 + (i % 4) * 1,
                1,
                -1 + Math.floor(i / 4) * 2
            );
            group.add(port);
        }
        
        // Антенны
        const antennaGeometry = new THREE.CylinderGeometry(0.1, 0.1, 3, 8);
        const antennaMaterial = new THREE.MeshPhongMaterial({ color: 0x64748b });
        
        for (let i = 0; i < 4; i++) {
            const antenna = new THREE.Mesh(antennaGeometry, antennaMaterial);
            antenna.position.set(
                -1.5 + i * 1,
                3,
                0
            );
            group.add(antenna);
        }
        
        return group;
    }
    
    createGenericElement(x, y, z, color) {
        const group = new THREE.Group();
        group.position.set(x, y, z);
        
        // Основная точка
        const pointGeometry = new THREE.SphereGeometry(2, 16, 16);
        const pointMaterial = new THREE.MeshPhongMaterial({
            color: color,
            emissive: color,
            emissiveIntensity: 0.2,
            shininess: 100
        });
        const point = new THREE.Mesh(pointGeometry, pointMaterial);
        group.add(point);
        
        // Внешнее кольцо
        const ringGeometry = new THREE.RingGeometry(2.5, 3, 16);
        const ringMaterial = new THREE.MeshBasicMaterial({
            color: color,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.5
        });
        const ring = new THREE.Mesh(ringGeometry, ringMaterial);
        ring.rotation.x = Math.PI / 2;
        group.add(ring);
        
        return group;
    }
    
    createNetworkConnections() {
        this.networkConnections.forEach((connection, index) => {
            const connection3D = this.createConnection3D(connection, index);
            if (connection3D) {
                this.scene.add(connection3D);
                connection.object3d = connection3D;
            }
        });
    }
    
    createConnection3D(connection, id) {
        const fromElement = this.networkElements.find(el => el.id === connection.from_element);
        const toElement = this.networkElements.find(el => el.id === connection.to_element);
        
        if (!fromElement || !toElement || !fromElement.object3d || !toElement.object3d) {
            console.warn(`Cannot create connection ${id}: elements not found`);
            return null;
        }
        
        const fromPos = fromElement.object3d.position;
        const toPos = toElement.object3d.position;
        
        // Определение цвета соединения
        let color;
        if (connection.connection_type in this.connectionColors) {
            color = this.connectionColors[connection.connection_type];
        } else if (connection.network_type in this.networkTypeColors) {
            color = this.networkTypeColors[connection.network_type];
        } else {
            color = 0x6ee7ff; // Цвет по умолчанию
        }
        
        // Создание кривой для соединения
        const curve = this.createConnectionCurve(fromPos, toPos, connection.connection_type);
        
        // Создание линии
        const lineGeometry = new THREE.TubeGeometry(curve, 20, 0.5, 8, false);
        const lineMaterial = new THREE.MeshBasicMaterial({
            color: color,
            transparent: true,
            opacity: this.settings.connectionOpacity,
            side: THREE.DoubleSide
        });
        
        const line = new THREE.Mesh(lineGeometry, lineMaterial);
        
        // Добавление пользовательских данных
        line.userData = {
            id: id,
            connectionId: connection.id,
            type: connection.connection_type,
            networkType: connection.network_type,
            fromElement: connection.from_element,
            toElement: connection.to_element,
            bandwidth: connection.bandwidth,
            latency: connection.latency,
            originalData: connection
        };
        
        return line;
    }
    
    createConnectionCurve(fromPos, toPos, connectionType) {
        const distance = fromPos.distanceTo(toPos);
        
        // Для спутниковых соединений создаем дугу
        if (connectionType === 'SATELLITE' && distance > 50) {
            const midPoint = new THREE.Vector3().addVectors(fromPos, toPos).multiplyScalar(0.5);
            const height = distance * 0.3;
            midPoint.normalize().multiplyScalar(100 + height);
            
            return new THREE.QuadraticBezierCurve3(fromPos, midPoint, toPos);
        }
        
        // Для остальных соединений - прямая линия с небольшой кривизной
        const midPoint = new THREE.Vector3().addVectors(fromPos, toPos).multiplyScalar(0.5);
        const height = distance * 0.1;
        midPoint.normalize().multiplyScalar(100 + height);
        
        return new THREE.QuadraticBezierCurve3(fromPos, midPoint, toPos);
    }
    
    clearNetworkElements() {
        // Удаление всех элементов сети из сцены
        this.networkElements.forEach(element => {
            if (element.object3d && element.object3d.parent) {
                element.object3d.parent.remove(element.object3d);
            }
        });
        
        // Удаление всех соединений
        this.networkConnections.forEach(connection => {
            if (connection.object3d && connection.object3d.parent) {
                connection.object3d.parent.remove(connection.object3d);
            }
        });
        
        // Очистка массивов
        this.networkElements = [];
        this.networkConnections = [];
        this.selectedElement = null;
    }
    
    filterConnections(networkType) {
        // Показать/скрыть соединения в зависимости от типа сети
        this.networkConnections.forEach(connection => {
            if (connection.object3d) {
                if (networkType === 'all' || connection.network_type === networkType) {
                    connection.object3d.visible = true;
                } else {
                    connection.object3d.visible = false;
                }
            }
        });
    }
    
    onCanvasClick(event) {
        if (!this.isInitialized) return;
        
        // Получение координат клика
        const rect = this.canvas.getBoundingClientRect();
        const x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        const y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        
        const mouse = new THREE.Vector2(x, y);
        const raycaster = new THREE.Raycaster();
        raycaster.setFromCamera(mouse, this.camera);
        
        // Поиск пересечений
        const intersects = raycaster.intersectObjects(this.scene.children, true);
        
        if (intersects.length > 0) {
            const intersect = intersects[0];
            
            // Поиск элемента сети в иерархии объектов
            let element = intersect.object;
            while (element && !element.userData?.elementId) {
                element = element.parent;
            }
            
            if (element && element.userData) {
                this.selectElement(element.userData);
            } else {
                this.deselectElement();
            }
        } else {
            this.deselectElement();
        }
    }
    
    selectElement(elementData) {
        // Снятие выделения с предыдущего элемента
        if (this.selectedElement) {
            this.deselectElement();
        }
        
        // Сохранение выбранного элемента
        this.selectedElement = elementData;
        
        // Подсветка элемента
        const elementObj = this.networkElements.find(el => el.id === elementData.elementId)?.object3d;
        if (elementObj) {
            this.highlightElement(elementObj, true);
        }
        
        // Вызов callback функции если она установлена
        if (typeof this.onElementClick === 'function') {
            this.onElementClick(elementData);
        }
        
        console.log('Selected element:', elementData);
    }
    
    deselectElement() {
        if (this.selectedElement) {
            // Убрать подсветку
            const elementObj = this.networkElements.find(el => el.id === this.selectedElement.elementId)?.object3d;
            if (elementObj) {
                this.highlightElement(elementObj, false);
            }
            
            this.selectedElement = null;
        }
    }
    
    highlightElement(elementObj, highlight) {
        // Простая реализация подсветки
        elementObj.traverse((child) => {
            if (child.isMesh) {
                if (highlight) {
                    child.material.emissive = new THREE.Color(0xffff00);
                    child.material.emissiveIntensity = 0.5;
                } else {
                    // Восстановление оригинальных цветов
                    // Здесь нужно хранить оригинальные материалы
                }
            }
        });
    }
    
    zoomIn() {
        this.controls.dollyIn(0.2);
    }
    
    zoomOut() {
        this.controls.dollyOut(0.2);
    }
    
    resetView() {
        this.controls.reset();
        this.camera.position.set(0, 0, 300);
        this.controls.update();
    }
    
    toggleOrbit() {
        this.settings.autoRotate = !this.settings.autoRotate;
        this.controls.autoRotate = this.settings.autoRotate;
        return this.settings.autoRotate;
    }
    
    toggleAtmosphere() {
        this.settings.showAtmosphere = !this.settings.showAtmosphere;
        if (this.atmosphere) {
            this.atmosphere.visible = this.settings.showAtmosphere;
        }
        return this.settings.showAtmosphere;
    }
    
    getStatistics() {
        const stats = {
            elements: this.networkElements.length,
            connections: this.networkConnections.length,
            satellites: this.networkElements.filter(el => el.type === 'SATELLITE').length,
            byType: {}
        };
        
        // Подсчет соединений по типам
        this.networkConnections.forEach(conn => {
            const type = conn.connection_type;
            stats.byType[type] = (stats.byType[type] || 0) + 1;
        });
        
        return stats;
    }
    
    onWindowResize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }
    
    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());
        
        // Вращение Земли
        if (this.earth) {
            this.earth.rotation.y += 0.0005 * this.settings.animationSpeed;
        }
        
        // Вращение облаков
        if (this.clouds) {
            this.clouds.rotation.y += 0.0003 * this.settings.animationSpeed;
        }
        
        // Вращение атмосферы
        if (this.atmosphere) {
            this.atmosphere.rotation.y += 0.0002 * this.settings.animationSpeed;
        }
        
        // Обновление управления
        if (this.controls) {
            this.controls.update();
        }
        
        // Рендеринг сцены
        if (this.renderer && this.scene && this.camera) {
            this.renderer.render(this.scene, this.camera);
        }
    }
    
    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        if (this.controls) {
            this.controls.dispose();
        }
        
        if (this.renderer) {
            this.renderer.dispose();
            this.renderer.forceContextLoss();
        }
        
        // Очистка сцены
        if (this.scene) {
            while (this.scene.children.length > 0) {
                this.scene.remove(this.scene.children[0]);
            }
        }
        
        this.isInitialized = false;
        console.log('Globe scene destroyed');
    }
}

// ===== ГЛОБАЛЬНЫЕ ФУНКЦИИ =====

// Инициализация глобуса
function initGlobe() {
    const canvas = document.getElementById('globe-canvas');
    const container = document.querySelector('.globe-container');
    
    if (!canvas || !container) {
        console.error('Globe canvas or container not found');
        return null;
    }
    
    try {
        window.globeScene = new GlobeScene(canvas, container);
        return window.globeScene;
    } catch (error) {
        console.error('Failed to initialize globe:', error);
        return null;
    }
}

// Загрузка демо-данных
function loadDemoData() {
    if (!window.globeScene) return;
    
    const demoData = {
        elements: [
            {
                id: 1,
                name: 'Спутник Starlink-1',
                type: 'SATELLITE',
                latitude: 40.0,
                longitude: -80.0,
                altitude: 550,
                description: 'Спутник группировки Starlink'
            },
            {
                id: 2,
                name: 'Наземная станция Москва',
                type: 'GROUND_STATION',
                latitude: 55.7558,
                longitude: 37.6173,
                altitude: 0,
                description: 'Основная наземная станция в Москве'
            },
            {
                id: 3,
                name: 'Маршрутизатор Минск',
                type: 'ROUTER',
                latitude: 53.9045,
                longitude: 27.5615,
                altitude: 0,
                description: 'Основной маршрутизатор в Минске'
            },
            {
                id: 4,
                name: 'Спутник связи',
                type: 'SATELLITE',
                latitude: 0,
                longitude: -70,
                altitude: 36000,
                description: 'Геостационарный спутник связи'
            }
        ],
        connections: [
            {
                id: 1,
                from_element: 1,
                to_element: 2,
                connection_type: 'SATELLITE',
                network_type: 'EXISTING',
                bandwidth: 100,
                latency: 30
            },
            {
                id: 2,
                from_element: 2,
                to_element: 3,
                connection_type: 'FIBER',
                network_type: 'EXISTING',
                bandwidth: 1000,
                latency: 5
            },
            {
                id: 3,
                from_element: 4,
                to_element: 2,
                connection_type: 'SATELLITE',
                network_type: 'PROPOSED',
                bandwidth: 500,
                latency: 250
            }
        ]
    };
    
    window.globeScene.loadNetworkData(demoData);
}

// Экспорт функций
window.GlobeScene = GlobeScene;
window.initGlobe = initGlobe;
window.loadDemoData = loadDemoData;

// Автоматическая инициализация при наличии canvas
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('globe-canvas')) {
        setTimeout(() => {
            const scene = initGlobe();
            if (scene) {
                // Загрузка демо-данных через 1 секунду
                setTimeout(loadDemoData, 1000);
            }
        }, 500);
    }
});
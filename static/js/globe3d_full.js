// Z96A Network Globe - Complete version with cables and controls
console.log('🌍 Z96A Network Globe loading...');

class NetworkGlobe {
    constructor(containerId) {
        console.log('Initializing for container:', containerId);
        
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error('Container not found!');
            return;
        }
        
        this.config = {
            earthRadius: 3.0,
            autoRotate: true,
            rotationSpeed: 0.002,
            showEquipment: true,
            showCables: true,
            currentNetwork: 'existing'
        };
        
        this.nodes = [];
        this.connections = [];
        this.equipment = [];
        
        this.initThreeJS();
        this.createEarthWithTexture();
        this.createControls();
        this.loadNetworkData();
        this.animate();
        
        console.log('✅ NetworkGlobe initialized');
    }
    
    initThreeJS() {
        // Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0a0a1a);
        this.scene.fog = new THREE.Fog(0x0a0a1a, 10, 50);
        
        // Camera
        this.camera = new THREE.PerspectiveCamera(
            75,
            this.container.clientWidth / this.container.clientHeight,
            0.1,
            1000
        );
        this.camera.position.set(0, 2, 8);
        
        // Renderer
        this.renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: true
        });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        this.container.appendChild(this.renderer.domElement);
        
        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
        this.scene.add(ambientLight);
        
        const sunLight = new THREE.DirectionalLight(0xffffff, 0.8);
        sunLight.position.set(10, 10, 10);
        this.scene.add(sunLight);
        
        // Stars
        this.createStarfield();
    }
    
    createEarthWithTexture() {
        const geometry = new THREE.SphereGeometry(this.config.earthRadius, 64, 64);
        
        // Try to load texture, fallback to color
        try {
            const textureLoader = new THREE.TextureLoader();
            // Try different paths
            const texturePaths = [
                '/static/images/earth_texture.jpg',
                '/static/images/earth.jpg',
                'https://raw.githubusercontent.com/zyaba1212/Diplommm3/main/static/images/earth_texture.jpg'
            ];
            
            let earthTexture = null;
            for (const path of texturePaths) {
                try {
                    earthTexture = textureLoader.load(path);
                    console.log('Earth texture loaded from:', path);
                    break;
                } catch (e) {
                    continue;
                }
            }
            
            const material = earthTexture 
                ? new THREE.MeshPhongMaterial({ map: earthTexture })
                : new THREE.MeshPhongMaterial({ 
                    color: 0x1a5fb4,
                    specular: 0x111111,
                    shininess: 30
                });
            
            this.earth = new THREE.Mesh(geometry, material);
        } catch (error) {
            console.warn('Texture loading failed, using colored sphere:', error);
            const material = new THREE.MeshPhongMaterial({ 
                color: 0x1a5fb4,
                specular: 0x111111,
                shininess: 30
            });
            this.earth = new THREE.Mesh(geometry, material);
        }
        
        this.scene.add(this.earth);
        
        // Atmosphere
        const atmosphereGeometry = new THREE.SphereGeometry(this.config.earthRadius * 1.02, 32, 32);
        const atmosphereMaterial = new THREE.MeshPhongMaterial({
            color: 0x4466ff,
            transparent: true,
            opacity: 0.1,
            side: THREE.BackSide
        });
        this.atmosphere = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial);
        this.scene.add(this.atmosphere);
        
        // Clouds
        const cloudGeometry = new THREE.SphereGeometry(this.config.earthRadius * 1.01, 32, 32);
        const cloudMaterial = new THREE.MeshPhongMaterial({
            color: 0xffffff,
            transparent: true,
            opacity: 0.2,
            side: THREE.DoubleSide
        });
        this.clouds = new THREE.Mesh(cloudGeometry, cloudMaterial);
        this.scene.add(this.clouds);
    }
    
    createStarfield() {
        const starsGeometry = new THREE.BufferGeometry();
        const starsCount = 1000;
        const positions = new Float32Array(starsCount * 3);
        
        for (let i = 0; i < starsCount * 3; i += 3) {
            positions[i] = (Math.random() - 0.5) * 200;
            positions[i + 1] = (Math.random() - 0.5) * 200;
            positions[i + 2] = (Math.random() - 0.5) * 200;
        }
        
        starsGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        const starsMaterial = new THREE.PointsMaterial({ color: 0xffffff, size: 0.1 });
        const stars = new THREE.Points(starsGeometry, starsMaterial);
        this.scene.add(stars);
    }
    
    createControls() {
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.rotateSpeed = 0.5;
        this.controls.minDistance = 4;
        this.controls.maxDistance = 20;
        this.controls.autoRotate = this.config.autoRotate;
        this.controls.autoRotateSpeed = 0.5;
    }
    
    async loadNetworkData() {
        try {
            const response = await fetch('/static/data/network_data.json');
            const data = await response.json();
            console.log('Network data loaded:', data);
            this.createNetworkElements(data);
        } catch (error) {
            console.error('Failed to load network data:', error);
            this.createSampleNetwork();
        }
    }
    
    createNetworkElements(data) {
        // Create nodes (cities)
        if (data.nodes) {
            data.nodes.forEach(node => {
                this.addNetworkNode(node);
            });
        }
        
        // Create cables (connections)
        if (data.connections) {
            data.connections.forEach(conn => {
                this.addNetworkCable(conn);
            });
        }
        
        // Create equipment
        if (data.equipment) {
            data.equipment.forEach(eq => {
                this.addEquipment(eq);
            });
        }
    }
    
    addNetworkNode(node) {
        const position = this.latLonToVector(node.latitude, node.longitude, this.config.earthRadius * 1.05);
        
        const geometry = new THREE.SphereGeometry(0.05, 8, 8);
        const material = new THREE.MeshPhongMaterial({ 
            color: node.type === 'datacenter' ? 0xff4444 : 0x44ff44,
            emissive: node.type === 'datacenter' ? 0x441111 : 0x114411
        });
        
        const marker = new THREE.Mesh(geometry, material);
        marker.position.copy(position);
        marker.userData = node;
        
        this.scene.add(marker);
        this.nodes.push(marker);
    }
    
    addNetworkCable(connection) {
        const fromPos = this.latLonToVector(connection.from.lat, connection.from.lon, this.config.earthRadius * 1.03);
        const toPos = this.latLonToVector(connection.to.lat, connection.to.lon, this.config.earthRadius * 1.03);
        
        // Create curved cable
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
        
        const points = curve.getPoints(20);
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        const material = new THREE.LineBasicMaterial({
            color: connection.type === 'undersea' ? 0x00ffff : 0xffff00,
            transparent: true,
            opacity: 0.7
        });
        
        const cable = new THREE.Line(geometry, material);
        cable.userData = connection;
        
        this.scene.add(cable);
        this.connections.push(cable);
    }
    
    addEquipment(equipment) {
        const position = this.latLonToVector(equipment.latitude, equipment.longitude, this.config.earthRadius * 1.08);
        
        let geometry, color;
        switch(equipment.type) {
            case 'router':
                geometry = new THREE.BoxGeometry(0.06, 0.04, 0.08);
                color = 0xff6600;
                break;
            case 'switch':
                geometry = new THREE.BoxGeometry(0.08, 0.02, 0.06);
                color = 0x00cc66;
                break;
            case 'satellite':
                geometry = new THREE.OctahedronGeometry(0.04);
                color = 0xff33cc;
                break;
            default:
                geometry = new THREE.BoxGeometry(0.04, 0.04, 0.04);
                color = 0x888888;
        }
        
        const material = new THREE.MeshPhongMaterial({ color: color });
        const equipmentObj = new THREE.Mesh(geometry, material);
        equipmentObj.position.copy(position);
        equipmentObj.rotation.y = Math.random() * Math.PI * 2;
        equipmentObj.userData = equipment;
        
        this.scene.add(equipmentObj);
        this.equipment.push(equipmentObj);
    }
    
    createSampleNetwork() {
        console.log('Creating sample network...');
        
        // Major cities as nodes
        const sampleNodes = [
            { name: "Москва", latitude: 55.7558, longitude: 37.6173, type: "datacenter" },
            { name: "Франкфурт", latitude: 50.1109, longitude: 8.6821, type: "ix" },
            { name: "Сингапур", latitude: 1.3521, longitude: 103.8198, type: "datacenter" },
            { name: "Нью-Йорк", latitude: 40.7128, longitude: -74.0060, type: "city" },
            { name: "Токио", latitude: 35.6762, longitude: 139.6503, type: "city" },
            { name: "Лондон", latitude: 51.5074, longitude: -0.1278, type: "ix" },
            { name: "Сан-Франциско", latitude: 37.7749, longitude: -122.4194, type: "datacenter" },
            { name: "Сидней", latitude: -33.8688, longitude: 151.2093, type: "city" }
        ];
        
        // Submarine cables
        const sampleConnections = [
            { from: { lat: 55.7558, lon: 37.6173 }, to: { lat: 50.1109, lon: 8.6821 }, type: "undersea" },
            { from: { lat: 50.1109, lon: 8.6821 }, to: { lat: 40.7128, lon: -74.0060 }, type: "undersea" },
            { from: { lat: 1.3521, lon: 103.8198 }, to: { lat: 35.6762, lon: 139.6503 }, type: "undersea" },
            { from: { lat: 40.7128, lon: -74.0060 }, to: { lat: 37.7749, lon: -122.4194 }, type: "terrestrial" },
            { from: { lat: 51.5074, lon: -0.1278 }, to: { lat: 40.7128, lon: -74.0060 }, type: "undersea" },
            { from: { lat: 37.7749, lon: -122.4194 }, to: { lat: 35.6762, lon: 139.6503 }, type: "undersea" },
            { from: { lat: 1.3521, lon: 103.8198 }, to: { lat: -33.8688, lon: 151.2093 }, type: "undersea" },
            { from: { lat: 50.1109, lon: 8.6821 }, to: { lat: 51.5074, lon: -0.1278 }, type: "undersea" }
        ];
        
        // Equipment
        const sampleEquipment = [
            { name: "Маршрутизатор", latitude: 55.7558, longitude: 37.6173, type: "router" },
            { name: "Коммутатор", latitude: 50.1109, longitude: 8.6821, type: "switch" },
            { name: "Спутник", latitude: 40.7128, longitude: -74.0060, type: "satellite" },
            { name: "Сервер", latitude: 1.3521, longitude: 103.8198, type: "server" }
        ];
        
        sampleNodes.forEach(node => this.addNetworkNode(node));
        sampleConnections.forEach(conn => this.addNetworkCable(conn));
        sampleEquipment.forEach(eq => this.addEquipment(eq));
    }
    
    latLonToVector(lat, lon, radius) {
        const phi = (90 - lat) * (Math.PI / 180);
        const theta = (lon + 180) * (Math.PI / 180);
        
        const x = -(radius * Math.sin(phi) * Math.cos(theta));
        const y = radius * Math.cos(phi);
        const z = radius * Math.sin(phi) * Math.sin(theta);
        
        return new THREE.Vector3(x, y, z);
    }
    
    // Public control methods
    toggleRotation() {
        this.config.autoRotate = !this.config.autoRotate;
        this.controls.autoRotate = this.config.autoRotate;
        console.log('Auto-rotation:', this.config.autoRotate ? 'ON' : 'OFF');
    }
    
    resetView() {
        this.controls.reset();
        this.camera.position.set(0, 2, 8);
    }
    
    zoomIn() {
        this.camera.position.multiplyScalar(0.9);
    }
    
    zoomOut() {
        this.camera.position.multiplyScalar(1.1);
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
    
    switchNetwork(type) {
        console.log('Switching to network:', type);
        this.config.currentNetwork = type;
        // Network switching logic here
    }
    
    animate() {
        requestAnimationFrame(() => this.animate());
        
        // Rotate Earth
        if (this.earth) {
            this.earth.rotation.y += this.config.rotationSpeed;
        }
        
        // Rotate clouds faster
        if (this.clouds) {
            this.clouds.rotation.y += this.config.rotationSpeed * 1.5;
        }
        
        // Rotate atmosphere slower
        if (this.atmosphere) {
            this.atmosphere.rotation.y += this.config.rotationSpeed * 0.5;
        }
        
        // Rotate equipment
        this.equipment.forEach(eq => {
            eq.rotation.y += 0.01;
        });
        
        // Update controls
        if (this.controls) {
            this.controls.update();
        }
        
        // Render
        this.renderer.render(this.scene, this.camera);
    }
    
    onWindowResize() {
        this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    }
}

// Make available globally
window.NetworkGlobe = NetworkGlobe;
console.log('✅ NetworkGlobe class ready');
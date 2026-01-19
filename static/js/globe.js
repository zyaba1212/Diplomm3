// 3D Globe with Three.js
class NetworkGlobe {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.globe = null;
        this.controls = null;
        this.isRotating = true;
        this.rotationSpeed = 0.001;
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.error('Container not found');
            return;
        }
        
        // Check if Three.js is available
        if (typeof THREE === 'undefined') {
            console.error('Three.js is not loaded');
            this.showFallback();
            return;
        }
        
        try {
            this.setupScene();
            this.createGlobe();
            this.createStars();
            this.setupLights();
            this.setupControls();
            this.animate();
            
            // Hide loading message
            const loading = this.container.querySelector('.globe-loading');
            if (loading) loading.style.display = 'none';
            
        } catch (error) {
            console.error('Error initializing globe:', error);
            this.showFallback();
        }
    }
    
    setupScene() {
        // Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0a0a1a);
        
        // Camera
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera = new THREE.PerspectiveCamera(45, width / height, 1, 2000);
        this.camera.position.z = 500;
        
        // Renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.container.appendChild(this.renderer.domElement);
        
        // Handle resize
        window.addEventListener('resize', () => this.onResize());
    }
    
    createGlobe() {
        const radius = 200;
        
        // Create Earth sphere
        const geometry = new THREE.SphereGeometry(radius, 64, 64);
        
        // Create texture (simulated)
        const canvas = document.createElement('canvas');
        canvas.width = 2048;
        canvas.height = 1024;
        const ctx = canvas.getContext('2d');
        
        // Draw basic Earth texture
        const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
        gradient.addColorStop(0, '#1a5fb4');
        gradient.addColorStop(0.5, '#26a269');
        gradient.addColorStop(1, '#1a5fb4');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Add continents
        ctx.fillStyle = '#2ec27e';
        // Simplified continents
        ctx.fillRect(canvas.width * 0.15, canvas.height * 0.3, canvas.width * 0.2, canvas.height * 0.4); // Americas
        ctx.fillRect(canvas.width * 0.5, canvas.height * 0.3, canvas.width * 0.25, canvas.height * 0.4); // Europe/Africa
        ctx.fillRect(canvas.width * 0.75, canvas.height * 0.25, canvas.width * 0.2, canvas.height * 0.5); // Asia/Australia
        
        const texture = new THREE.CanvasTexture(canvas);
        const material = new THREE.MeshPhongMaterial({
            map: texture,
            specular: new THREE.Color(0x333333),
            shininess: 5
        });
        
        this.globe = new THREE.Mesh(geometry, material);
        this.scene.add(this.globe);
        
        // Add atmosphere
        const atmosphereGeometry = new THREE.SphereGeometry(radius * 1.02, 32, 32);
        const atmosphereMaterial = new THREE.MeshBasicMaterial({
            color: 0x0099ff,
            transparent: true,
            opacity: 0.1
        });
        const atmosphere = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial);
        this.scene.add(atmosphere);
        
        // Add some network nodes (example)
        this.addExampleNodes();
    }
    
    createStars() {
        const starGeometry = new THREE.BufferGeometry();
        const starCount = 5000;
        const positions = new Float32Array(starCount * 3);
        
        for (let i = 0; i < starCount; i++) {
            positions[i * 3] = (Math.random() - 0.5) * 2000;
            positions[i * 3 + 1] = (Math.random() - 0.5) * 2000;
            positions[i * 3 + 2] = (Math.random() - 0.5) * 2000;
        }
        
        starGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        
        const starMaterial = new THREE.PointsMaterial({
            color: 0xffffff,
            size: 1,
            sizeAttenuation: true
        });
        
        const stars = new THREE.Points(starGeometry, starMaterial);
        this.scene.add(stars);
    }
    
    setupLights() {
        const ambientLight = new THREE.AmbientLight(0x404040);
        this.scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
        directionalLight.position.set(5, 3, 5);
        this.scene.add(directionalLight);
    }
    
    setupControls() {
        // Simple auto-rotation
        // For orbit controls, you would need to import OrbitControls
    }
    
    addExampleNodes() {
        // Example network nodes
        const nodes = [
            { lat: 40.7128, lon: -74.0060, color: 0x0099ff, size: 5 }, // New York
            { lat: 51.5074, lon: -0.1278, color: 0x0099ff, size: 5 }, // London
            { lat: 35.6762, lon: 139.6503, color: 0x0099ff, size: 5 }, // Tokyo
            { lat: 55.7558, lon: 37.6173, color: 0xff4444, size: 6 }, // Moscow
            { lat: 52.5200, lon: 13.4050, color: 0xff4444, size: 6 }, // Berlin
            { lat: 1.3521, lon: 103.8198, color: 0x9d4edd, size: 5 }, // Singapore
        ];
        
        nodes.forEach(node => {
            this.addNode(node);
        });
    }
    
    addNode(nodeData) {
        const { lat, lon, color, size } = nodeData;
        
        // Convert lat/lon to 3D coordinates
        const phi = (90 - lat) * (Math.PI / 180);
        const theta = (lon + 180) * (Math.PI / 180);
        
        const radius = 205; // Slightly above Earth surface
        const x = -(radius * Math.sin(phi) * Math.cos(theta));
        const y = radius * Math.cos(phi);
        const z = radius * Math.sin(phi) * Math.sin(theta);
        
        // Create node sphere
        const geometry = new THREE.SphereGeometry(size || 3, 16, 16);
        const material = new THREE.MeshBasicMaterial({ color });
        const node = new THREE.Mesh(geometry, material);
        node.position.set(x, y, z);
        
        this.scene.add(node);
        
        // Add glow effect
        const glowGeometry = new THREE.SphereGeometry((size || 3) * 1.5, 16, 16);
        const glowMaterial = new THREE.MeshBasicMaterial({
            color,
            transparent: true,
            opacity: 0.3
        });
        const glow = new THREE.Mesh(glowGeometry, glowMaterial);
        glow.position.set(x, y, z);
        this.scene.add(glow);
    }
    
    animate() {
        requestAnimationFrame(() => this.animate());
        
        // Rotate globe
        if (this.isRotating && this.globe) {
            this.globe.rotation.y += this.rotationSpeed;
        }
        
        // Render scene
        if (this.renderer && this.scene && this.camera) {
            this.renderer.render(this.scene, this.camera);
        }
    }
    
    onResize() {
        if (!this.camera || !this.renderer || !this.container) return;
        
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }
    
    showFallback() {
        const loading = this.container.querySelector('.globe-loading');
        if (loading) {
            loading.innerHTML = `
                <div style="color: #ff9900; margin-bottom: 20px;">
                    <div style="font-size: 48px;">🌍</div>
                    <p><strong>3D Globe Preview</strong></p>
                </div>
                <p>Full 3D visualization requires Three.js library.</p>
                <p>For now, showing interactive map preview.</p>
                <div style="margin-top: 20px; padding: 20px; background: rgba(0,0,0,0.3); border-radius: 10px;">
                    <p>🌐 <strong>Existing Network:</strong> Blue nodes</p>
                    <p>🚀 <strong>Proposed Network:</strong> Purple nodes</p>
                    <p>🛰️ <strong>Satellite Links:</strong> Orange lines</p>
                    <p>🌊 <strong>Submarine Cables:</strong> Green lines</p>
                </div>
            `;
        }
    }
    
    setRotation(enabled) {
        this.isRotating = enabled;
    }
    
    resetView() {
        if (this.camera) {
            this.camera.position.set(0, 0, 500);
            this.camera.lookAt(0, 0, 0);
        }
    }
}

// Initialize globe when Three.js is loaded
function initGlobe() {
    window.networkGlobe = new NetworkGlobe('globe-container');
}

// Load Three.js and initialize
if (typeof THREE !== 'undefined') {
    initGlobe();
} else {
    // Load Three.js dynamically
    const script = document.createElement('script');
    script.src = 'https://unpkg.com/three@0.155.0/build/three.min.js';
    script.onload = initGlobe;
    document.head.appendChild(script);
}
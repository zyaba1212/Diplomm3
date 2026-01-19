// Three.js основная сцена для глобуса
let scene, camera, renderer, controls;
let earthMesh;
let rotationEnabled = true;
let currentNetworkType = 'existing';
let cables = [];

// Инициализация сцены
function initGlobe() {
    // 1. Создаём сцену
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a1a);
    
// ДОБАВЬ ПОСЛЕ СОЗДАНИЯ СЦЕНЫ (после scene.background = ...)

// Звёздное небо
function createStarfield() {
    const starGeometry = new THREE.BufferGeometry();
    const starCount = 10000;
    const positions = new Float32Array(starCount * 3);
    
    for (let i = 0; i < starCount * 3; i += 3) {
        // Случайные координаты в сфере
        const radius = 100 + Math.random() * 900;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos((Math.random() * 2) - 1);
        
        positions[i] = radius * Math.sin(phi) * Math.cos(theta);
        positions[i+1] = radius * Math.sin(phi) * Math.sin(theta);
        positions[i+2] = radius * Math.cos(phi);
    }
    
    starGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    
    const starMaterial = new THREE.PointsMaterial({
        color: 0xffffff,
        size: 0.7,
        transparent: true
    });
    
    const stars = new THREE.Points(starGeometry, starMaterial);
    scene.add(stars);
}

// Стратосфера (слои атмосферы)
function createAtmosphereLayers() {
    // Тропосфера (0-12km)
    const tropoGeometry = new THREE.SphereGeometry(5.05, 32, 32);
    const tropoMaterial = new THREE.MeshBasicMaterial({
        color: 0x87ceeb,
        transparent: true,
        opacity: 0.05,
        side: THREE.BackSide
    });
    const tropoSphere = new THREE.Mesh(tropoGeometry, tropoMaterial);
    scene.add(tropoSphere);
    
    // Стратосфера (12-50km)
    const stratoGeometry = new THREE.SphereGeometry(5.08, 32, 32);
    const stratoMaterial = new THREE.MeshBasicMaterial({
        color: 0x4682b4,
        transparent: true,
        opacity: 0.03,
        side: THREE.BackSide
    });
    const stratoSphere = new THREE.Mesh(stratoGeometry, stratoMaterial);
    scene.add(stratoSphere);
    
    // Спутники на низкой орбите (LEO)
    createSatellites();
}

// Спутники
function createSatellites() {
    const satCount = 50;
    
    for (let i = 0; i < satCount; i++) {
        // Случайная орбита
        const altitude = 5.2 + Math.random() * 0.5; // Выше атмосферы
        const angle = Math.random() * Math.PI * 2;
        const tilt = Math.random() * Math.PI * 0.1;
        
        const satGeometry = new THREE.BoxGeometry(0.02, 0.02, 0.05);
        const satMaterial = new THREE.MeshBasicMaterial({ 
            color: i % 3 === 0 ? 0xff4444 : (i % 3 === 1 ? 0x44ff44 : 0x4444ff) 
        });
        
        const satellite = new THREE.Mesh(satGeometry, satMaterial);
        
        // Позиционируем на орбите
        const radius = altitude;
        satellite.position.x = radius * Math.cos(angle);
        satellite.position.z = radius * Math.sin(angle);
        satellite.position.y = radius * Math.sin(tilt);
        
        // Сохраняем параметры для анимации
        satellite.userData = {
            orbitRadius: radius,
            angle: angle,
            speed: 0.001 + Math.random() * 0.002,
            tilt: tilt
        };
        
        scene.add(satellite);
    }
}

// Анимация спутников
function animateSatellites() {
    scene.children.forEach(child => {
        if (child.userData && child.userData.orbitRadius) {
            // Обновляем позицию по орбите
            child.userData.angle += child.userData.speed;
            
            child.position.x = child.userData.orbitRadius * Math.cos(child.userData.angle);
            child.position.z = child.userData.orbitRadius * Math.sin(child.userData.angle);
            child.position.y = child.userData.orbitRadius * Math.sin(child.userData.tilt) * Math.cos(child.userData.angle * 0.5);
            
            // Поворачиваем к Земле
            child.lookAt(0, 0, 0);
        }
    });
}

    // 2. Создаём камеру
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 15;
    
    // 3. Создаём рендерер
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.getElementById('globe-container').appendChild(renderer.domElement);
    
    // 4. Элементы управления камерой
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 8;
    controls.maxDistance = 50;
    
    // 5. Освещение
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(5, 3, 5);
    scene.add(directionalLight);
    
    // 6. Создаём Землю
    createEarth();
    
    // 7. Создаём кабели (используем функции из globe3d_full.js)
    if (typeof createAllCables === 'function') {
        createAllCables();
    }
    
    // 8. Создаём оборудование в ключевых городах
    createNetworkEquipment();
    
    // 9. Запускаем анимацию
    animate();
    
    // 10. Обработка изменения размера окна
    window.addEventListener('resize', onWindowResize);
}

// Создание Земли
function createEarth() {
    const geometry = new THREE.SphereGeometry(5, 64, 64);
    
    // Текстура Земли
    const textureLoader = new THREE.TextureLoader();
    const earthTexture = textureLoader.load('https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/planets/earth_atmos_2048.jpg');
    const earthBump = textureLoader.load('https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/planets/earth_normal_2048.jpg');
    const earthSpec = textureLoader.load('https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/planets/earth_specular_2048.jpg');
    
    const material = new THREE.MeshPhongMaterial({
        map: earthTexture,
        bumpMap: earthBump,
        bumpScale: 0.05,
        specularMap: earthSpec,
        specular: new THREE.Color(0x333333),
        shininess: 5
    });
    
    earthMesh = new THREE.Mesh(geometry, material);
    scene.add(earthMesh);
    
    // Добавляем атмосферу
    const atmosphereGeometry = new THREE.SphereGeometry(5.1, 64, 64);
    const atmosphereMaterial = new THREE.MeshPhongMaterial({
        color: 0x87ceeb,
        transparent: true,
        opacity: 0.1
    });
    const atmosphere = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial);
    scene.add(atmosphere);
}

// Создание оборудования в ключевых городах
function createNetworkEquipment() {
    const cities = [
        // Северная Америка
        {name: "Нью-Йорк", lat: 40.7, lon: -74, type: "hub"},
        {name: "Ашберн", lat: 39, lon: -77.5, type: "datacenter"},
        {name: "Лос-Анджелес", lat: 34, lon: -118, type: "hub"},
        
        // Европа
        {name: "Франкфурт", lat: 50.1, lon: 8.7, type: "ix"},
        {name: "Лондон", lat: 51.5, lon: -0.1, type: "hub"},
        {name: "Амстердам", lat: 52.4, lon: 4.9, type: "ix"},
        
        // Азия
        {name: "Сингапур", lat: 1.3, lon: 103.8, type: "hub"},
        {name: "Гонконг", lat: 22.3, lon: 114.2, type: "hub"},
        {name: "Токио", lat: 35.7, lon: 139.8, type: "hub"},
        
        // Россия
        {name: "Москва", lat: 55.8, lon: 37.6, type: "ix"},
        {name: "Санкт-Петербург", lat: 59.9, lon: 30.3, type: "node"},
        {name: "Владивосток", lat: 43.1, lon: 131.9, type: "gateway"},
    ];
    
    cities.forEach(city => {
        createCityMarker(city.lat, city.lon, city.name, city.type);
    });
}

// Создание маркера города
function createCityMarker(lat, lon, name, type) {
    const radius = 5.01; // На поверхности Земли
    
    const position = latLonToVector3(lat, lon, radius);
    
    // Создаём маркер как часть поверхности Земли
    const markerGroup = new THREE.Group();
    
    // Точка на поверхности
    const geometry = new THREE.ConeGeometry(0.03, 0.1, 4);
    geometry.rotateX(Math.PI); // Переворачиваем конус
    
    let color;
    let height = 0.1;
    
    switch(type) {
        case 'hub': 
            color = 0x00ff00; 
            height = 0.15;
            break;
        case 'ix': 
            color = 0xff9900; 
            height = 0.12;
            break;
        case 'datacenter': 
            color = 0x3498db; 
            geometry = new THREE.BoxGeometry(0.05, 0.05, 0.05);
            break;
        case 'gateway': 
            color = 0x9b59b6; 
            geometry = new THREE.CylinderGeometry(0.02, 0.04, 0.08, 6);
            break;
        default: 
            color = 0xffffff;
    }
    
    const material = new THREE.MeshBasicMaterial({ color: color });
    const marker = new THREE.Mesh(geometry, material);
    
    // Позиционируем на поверхности
    marker.position.copy(position);
    
    // Нормализуем позицию чтобы маркер был на поверхности
    marker.position.normalize().multiplyScalar(radius);
    
    // Поворачиваем маркер наружу от центра Земли
    marker.lookAt(marker.position.clone().multiplyScalar(2));
    
    markerGroup.add(marker);
    
    // Добавляем подпись (текст)
    if (typeof createTextLabel === 'function') {
        const label = createTextLabel(name, position);
        if (label) markerGroup.add(label);
    }
    
    // Сохраняем информацию
    marker.userData = {
        type: 'equipment',
        name: name,
        cityType: type,
        lat: lat,
        lon: lon,
        details: getEquipmentDetails(type, name)
    };
    
    scene.add(markerGroup);
    
    // Добавляем луч/соединение
    createConnectionBeam(position, color);
}

function createConnectionBeam(position, color) {
    const beamHeight = 0.3;
    const beamGeometry = new THREE.CylinderGeometry(0.005, 0.005, beamHeight, 8);
    const beamMaterial = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.5
    });
    
    const beam = new THREE.Mesh(beamGeometry, beamMaterial);
    beam.position.copy(position);
    
    // Вытягиваем луч от поверхности
    beam.position.normalize().multiplyScalar(5 + beamHeight/2);
    beam.lookAt(0, 0, 0);
    beam.rotateX(Math.PI/2);
    
    scene.add(beam);
}

// Конвертация координат в 3D (должна быть в globe3d_full.js, но на всякий случай)
function latLonToVector3(lat, lon, radius) {
    if (typeof window.latLonToVector3 === 'function') {
        return window.latLonToVector3(lat, lon, radius);
    }
    
    // Фолбэк если функция не определена
    const phi = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 180) * (Math.PI / 180);
    
    const x = -(radius * Math.sin(phi) * Math.cos(theta));
    const y = radius * Math.cos(phi);
    const z = radius * Math.sin(phi) * Math.sin(theta);
    
    return new THREE.Vector3(x, y, z);
}

// Анимация
function animate() {
    requestAnimationFrame(animate);
    
    if (rotationEnabled && earthMesh) {
        earthMesh.rotation.y += 0.001;
    }
    
    controls.update();
    renderer.render(scene, camera);
}

// Обработка изменения размера окна
function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

// Функции управления из интерфейса
function toggleRotation(enabled) {
    rotationEnabled = enabled;
}

function switchNetwork() {
    currentNetworkType = currentNetworkType === 'existing' ? 'proposed' : 'existing';
    
    // Здесь можно менять видимость элементов в зависимости от типа сети
    // Например, показывать/скрывать спутники Starlink
    alert('Переключено на сеть: ' + (currentNetworkType === 'existing' ? 'Существующая' : 'Предложенная'));
}

function setZoom(level) {
    const zoomMap = {
        1: 30, 2: 25, 3: 20, 4: 15, 5: 10,
        6: 8, 7: 6, 8: 5, 9: 4, 10: 3
    };
    
    if (controls && zoomMap[level]) {
        controls.maxDistance = zoomMap[level];
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем что Three.js загружен
    if (typeof THREE === 'undefined') {
        console.error('Three.js не загружен');
        return;
    }
    
    // Запускаем инициализацию
    initGlobe();
    
    // Подключаем обработчики кнопок
    const rotationBtn = document.getElementById('toggle-rotation');
    if (rotationBtn) {
        rotationBtn.addEventListener('click', function() {
            rotationEnabled = !rotationEnabled;
            this.textContent = `Вращение: ${rotationEnabled ? 'ВКЛ' : 'ВЫКЛ'}`;
        });
    }
    
    const networkBtn = document.getElementById('switch-network');
    if (networkBtn) {
        networkBtn.addEventListener('click', switchNetwork);
    }
    
    const zoomSlider = document.getElementById('zoom');
    if (zoomSlider) {
        zoomSlider.addEventListener('input', function(e) {
            setZoom(parseInt(e.target.value));
        });
    }
});

// В конец globe_main.js добавь
function setupControls() {
    // Кнопка вращения
    const rotationBtn = document.getElementById('toggle-rotation');
    if (rotationBtn) {
        rotationBtn.addEventListener('click', function() {
            rotationEnabled = !rotationEnabled;
            this.textContent = `Вращение: ${rotationEnabled ? 'ВКЛ' : 'ВЫКЛ'}`;
        });
    }
    
    // Кнопка кабелей
    const cablesBtn = document.getElementById('toggle-cables');
    if (cablesBtn) {
        cablesBtn.addEventListener('click', function() {
            // Переключаем видимость кабелей
            cables.forEach(cable => {
                cable.visible = !cable.visible;
            });
            this.textContent = `Кабели: ${cables[0]?.visible ? 'ВКЛ' : 'ВЫКЛ'}`;
        });
    }
    
    // Кнопка оборудования
    const equipmentBtn = document.getElementById('toggle-equipment');
    if (equipmentBtn) {
        equipmentBtn.addEventListener('click', function() {
            // Находим всё оборудование и переключаем
            scene.children.forEach(child => {
                if (child.userData && child.userData.type === 'equipment') {
                    child.visible = !child.visible;
                }
            });
        });
    }
    
    // Переключение сетей
    const networkBtn = document.getElementById('switch-network');
    if (networkBtn) {
        networkBtn.addEventListener('click', function() {
            currentNetworkType = currentNetworkType === 'existing' ? 'proposed' : 'existing';
            
            // Показываем/скрываем спутники Starlink
            const starlinkSats = scene.children.filter(child => 
                child.userData && child.userData.isStarlink
            );
            
            if (currentNetworkType === 'proposed') {
                // Показываем предложенную сеть (спутники Starlink)
                starlinkSats.forEach(sat => sat.visible = true);
                this.style.background = 'linear-gradient(135deg, #FF9900, #FF4444)';
                this.textContent = 'Сеть: Предложенная (Starlink)';
            } else {
                // Показываем существующую сеть
                starlinkSats.forEach(sat => sat.visible = false);
                this.style.background = 'linear-gradient(135deg, #9945FF, #14F195)';
                this.textContent = 'Сеть: Существующая';
            }
        });
    }
    
    // Зум
    const zoomSlider = document.getElementById('zoom');
    if (zoomSlider) {
        zoomSlider.addEventListener('input', function(e) {
            const zoomLevel = parseInt(e.target.value);
            if (controls) {
                controls.maxDistance = 30 - zoomLevel * 2;
                controls.minDistance = 3 + zoomLevel * 0.5;
            }
        });
    }
}

// Экспортируем функции для использования из HTML
window.toggleRotation = toggleRotation;
window.switchNetwork = switchNetwork;
window.setZoom = setZoom;
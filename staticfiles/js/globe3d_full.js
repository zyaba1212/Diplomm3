// ВСТАВЬТЕ ЭТОТ КОД в D:\Diplom3\static\js\globe3d_full.js
// В любом месте после создания сцены, но перед анимацией
// Например, после строки где создаётся earthMesh

function createSubmarineCable(startLat, startLon, endLat, endLon, color = 0x3498db, name = "") {
    // Конвертируем координаты в 3D точки на сфере
    const radius = 5.05; // Чуть больше Земли
    
    const startPoint = latLonToVector3(startLat, startLon, radius);
    const endPoint = latLonToVector3(endLat, endLon, radius);
    
    // Создаём кривую между точками
    const curve = new THREE.CatmullRomCurve3([
        startPoint,
        new THREE.Vector3(
            (startPoint.x + endPoint.x) / 2 * 1.1,
            (startPoint.y + endPoint.y) / 2 * 1.1,
            (startPoint.z + endPoint.z) / 2 * 1.1
        ), // Контрольная точка для изгиба
        endPoint
    ]);
    
    const points = curve.getPoints(50);
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    
    const material = new THREE.LineBasicMaterial({
        color: color,
        linewidth: 2,
        transparent: true,
        opacity: 0.7
    });
    
    const cable = new THREE.Line(geometry, material);
    cable.name = name || `cable_${startLat},${startLon}-${endLat},${endLon}`;
    
    // Добавляем интерактивность
    cable.userData = {
        type: 'submarine_cable',
        name: name,
        start: [startLat, startLon],
        end: [endLat, endLon]
    };
    
    scene.add(cable);
    return cable;
}

// Функция для конвертации координат
function latLonToVector3(lat, lon, radius) {
    const phi = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 180) * (Math.PI / 180);
    
    const x = -(radius * Math.sin(phi) * Math.cos(theta));
    const y = radius * Math.cos(phi);
    const z = radius * Math.sin(phi) * Math.sin(theta);
    
    return new THREE.Vector3(x, y, z);
}

// ОСНОВНЫЕ ПОДВОДНЫЕ КАБЕЛИ (на основе твоего исследования)
const submarineCables = [
    // Атлантические
    {name: "MAREA", start: [40, -74], end: [51, -4], color: 0x3498db}, // NY-London
    {name: "Apollo", start: [41, -70], end: [49, 2], color: 0x2ecc71}, // US-France
    {name: "Dunant", start: [37, -76], end: [46, -1], color: 0x9b59b6}, // Google cable
    
    // Тихоокеанские
    {name: "FASTER", start: [34, -118], end: [35, 139], color: 0xe74c3c}, // LA-Tokyo
    {name: "JUPITER", start: [37, -122], end: [33, 130], color: 0xf39c12}, // US-Japan-Philippines
    {name: "Southern Cross", start: [-33, 151], end: [21, -158], color: 0x1abc9c}, // Australia-Hawaii
    
    // Азиатские
    {name: "SEA-ME-WE 3", start: [43, 5], end: [1, 103], color: 0xe74c3c}, // Europe-Singapore
    {name: "Asia Pacific Gateway", start: [22, 114], end: [1, 103], color: 0x2ecc71}, // HK-Singapore
    {name: "FLAG FEA", start: [30, 31], end: [1, 103], color: 0x9b59b6}, // Egypt-Singapore
    
    // Африканские
    {name: "2Africa", start: [-34, 18], end: [43, 5], color: 0xf1c40f}, // Africa-Europe
    {name: "EASSy", start: [-4, 39], end: [-34, 18], color: 0x1abc9c}, // East Africa
    
    // Латинская Америка
    {name: "BRUSA", start: [25, -80], end: [-3, -60], color: 0xe67e22}, // Miami-Brazil
    {name: "South America-1", start: [25, -80], end: [-34, -58], color: 0x95a5a6}, // Miami-Argentina
];

// СОЗДАЁМ ВСЕ КАБЕЛИ
function createAllCables() {
    submarineCables.forEach(cable => {
        createSubmarineCable(
            cable.start[0], cable.start[1],
            cable.end[0], cable.end[1],
            cable.color, cable.name
        );
    });
}

// ВЫЗОВИТЕ ЭТУ ФУНКЦИЮ ПОСЛЕ СОЗДАНИЯ ЗЕМЛИ
// Найдите в коде функцию init() или подобную и добавьте:
// createAllCables();
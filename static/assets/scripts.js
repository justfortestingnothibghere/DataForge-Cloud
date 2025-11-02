// Global scripts
document.addEventListener('DOMContentLoaded', () => {
    console.log('DataForge loaded 💀');
    // Drag-drop for upload zones if needed
    const dropZones = document.querySelectorAll('[data-drop-zone]');
    dropZones.forEach(zone => {
        zone.addEventListener('dragover', e => e.preventDefault());
        zone.addEventListener('drop', e => {
            e.preventDefault();
            // Handle files
            const files = e.dataTransfer.files;
            // Trigger file input
        });
    });
});

// Cookie helper
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}
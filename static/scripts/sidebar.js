function toggleSidebar() {
    // Get the sidebar and overlay elements by their IDs
    var sidebar = document.getElementById('mobileSidebar');
    var overlay = document.getElementById('sidebarOverlay');
    
    // Toggle the .open class on the sidebar (slides in/out)
    sidebar.classList.toggle('open');
    
    // Toggle the .show class on the overlay
    overlay.classList.toggle('show');
    
    // OPTIONAL: Toggle .sidebar-open on <body> to disable background scroll
    document.body.classList.toggle('sidebar-open');
}

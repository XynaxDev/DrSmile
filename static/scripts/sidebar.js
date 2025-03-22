// Your existing function remains the same
function toggleSidebar() {
    var sidebar = document.getElementById('mobileSidebar');
    var overlay = document.getElementById('sidebarOverlay');

    // Toggle the .open class on the sidebar (slides in/out)
    sidebar.classList.toggle('open');

    // Toggle the .show class on the overlay
    overlay.classList.toggle('show');

    // OPTIONAL: Prevent background scroll
    document.body.classList.toggle('sidebar-open');
}

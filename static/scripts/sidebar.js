function toggleSidebar() {
    var sidebar = document.getElementById('mobileSidebar');
    var overlay = document.getElementById('sidebarOverlay');

    sidebar.classList.toggle('open');

    overlay.classList.toggle('show');

    document.body.classList.toggle('sidebar-open');
}

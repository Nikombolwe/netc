// JavaScript logic for Admin Dashboard

document.addEventListener("DOMContentLoaded", function () {
    console.log("Admin Dashboard Loaded Successfully.");

    // Kitufe cha Quick Refresh ya Logs Table
    const refreshBtn = document.getElementById("refresh-logs-btn");
    if (refreshBtn) {
        refreshBtn.addEventListener("click", function () {
            this.classList.add("animate-spin");
            setTimeout(() => {
                location.reload();
            }, 500);
        });
    }
});
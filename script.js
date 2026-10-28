document.addEventListener("DOMContentLoaded", () => {
    // Show / Hide password
    document.querySelectorAll("[data-password-toggle]").forEach((button) => {
        button.addEventListener("click", () => {
            const input = button.parentElement.querySelector("input");

            if (!input) return;

            const showing = input.type === "password";
            input.type = showing ? "text" : "password";
            button.textContent = showing ? "HIDE" : "SHOW";
            button.setAttribute(
                "aria-label",
                showing ? "Hide password" : "Show password"
            );
        });
    });

    // Animate dashboard statistics
    document.querySelectorAll("[data-count]").forEach((element) => {
        const target = Number(element.dataset.count);

        if (!Number.isFinite(target) || target < 0) return;

        const duration = 900;
        const start = performance.now();

        function animate(now) {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);

            element.textContent = Math.round(target * eased)
                .toLocaleString();

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        }

        requestAnimationFrame(animate);
    });

    // Highlight the selected dashboard navigation link
    const links = document.querySelectorAll(".nav-link");

    links.forEach((link) => {
        link.addEventListener("click", () => {
            links.forEach((item) => item.classList.remove("active"));
            link.classList.add("active");
        });
    });

    // Prevent accidental repeated clicks while submitting login
    const loginForm = document.querySelector(".login-form");

    if (loginForm) {
        loginForm.addEventListener("submit", () => {
            const button = loginForm.querySelector(
                'button[type="submit"]'
            );

            if (!button) return;

            button.disabled = true;
            button.querySelector("span").textContent =
                "AUTHENTICATING...";
        });
    }

    // Subtle pointer glow on larger screens
    if (window.matchMedia("(pointer: fine)").matches) {
        document.querySelectorAll(".metric-card, .login-card, .panel")
            .forEach((card) => {
                card.addEventListener("pointermove", (event) => {
                    const rect = card.getBoundingClientRect();

                    card.style.setProperty(
                        "--pointer-x",
                        `${event.clientX - rect.left}px`
                    );

                    card.style.setProperty(
                        "--pointer-y",
                        `${event.clientY - rect.top}px`
                    );
                });
            });
    }

    console.info("BruteForceDefense educational demo loaded.");
});
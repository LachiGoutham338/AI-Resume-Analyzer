document.querySelectorAll("[data-copy]").forEach(button => {
  button.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(button.dataset.copy);
      const old = button.textContent;
      button.textContent = "Copied!";
      setTimeout(() => button.textContent = old, 1300);
    } catch (e) {
      button.textContent = "Select and copy";
    }
  });
});
document.querySelectorAll(".flash").forEach(item => {
  setTimeout(() => { item.style.opacity = "0.92"; }, 3000);
});

document.addEventListener("DOMContentLoaded", () => {
  const bookmarks = document.querySelectorAll(".bookmark");

  bookmarks.forEach((bookmark) => {
    bookmark.addEventListener("click", () => {
      const title = bookmark.getAttribute("data-title");
      const summary = bookmark.getAttribute("data-summary");
      const url = bookmark.getAttribute("data-url");

      const article = { title, summary, url };

      fetch("/save_article", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(article),
      }).then((response) => {
        if (response.ok) {
          alert("Article saved!");
        } else {
          alert("Failed to save article.");
        }
      });
    });
  });
});

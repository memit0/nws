document.addEventListener("DOMContentLoaded", function () {
    const searchContainer = document.querySelector(".search-container");
    const searchBar = document.querySelector(".search-bar");
  
    let timeout;
  
    const showSearchBar = () => {
      clearTimeout(timeout);
      searchBar.classList.add("hover");
    };
  
    const hideSearchBar = () => {
      timeout = setTimeout(() => {
        if (!searchBar.matches(":hover") && !searchContainer.matches(":hover")) {
          searchBar.classList.remove("hover");
        }
      }, 300); // Adjust the delay time as needed
    };
  
    searchContainer.addEventListener("mouseover", showSearchBar);
    searchContainer.addEventListener("mouseout", hideSearchBar);
    searchBar.addEventListener("mouseover", showSearchBar);
    searchBar.addEventListener("mouseout", hideSearchBar);
  
    // Add event listener for bookmark buttons
    const bookmarkButtons = document.querySelectorAll(".bookmark");
    bookmarkButtons.forEach((button) => {
      button.addEventListener("click", function () {
        const articleData = {
          title: button.getAttribute("data-title"),
          summary: button.getAttribute("data-summary"),
          url: button.getAttribute("data-url"),
        };
  
        fetch("/save_article", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(articleData),
        })
          .then((response) => {
            if (response.status === 204) {
              alert("Article saved successfully!");
            } else {
              alert("Failed to save article.");
            }
          })
          .catch((error) => {
            console.error("Error saving article:", error);
            alert("An error occurred while saving the article.");
          });
      });
    });
  
    // Add event listener for remove-article buttons
    const removeButtons = document.querySelectorAll(".remove-article");
    removeButtons.forEach((button) => {
      button.addEventListener("click", function () {
        const articleData = {
          title: button.getAttribute("data-title"),
          url: button.getAttribute("data-url"),
        };
  
        fetch("/remove_article", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(articleData),
        })
          .then((response) => {
            if (response.status === 204) {
              alert("Article removed successfully!");
              button.parentElement.remove(); // Remove the article from the DOM
            } else {
              alert("Failed to remove article.");
            }
          })
          .catch((error) => {
            console.error("Error removing article:", error);
            alert("An error occurred while removing the article.");
          });
      });
    });
  });
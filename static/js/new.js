document.addEventListener("DOMContentLoaded", function () {
    const recentContainer = document.getElementById("recent-container");
    const pagination = document.getElementById("recent-pagination");
  
    let currentPage = 1;
    let totalPages = 1;
    let totalResults = 0;
  
  // Додай під DOMContentLoaded
fetch("/api/recommendations/")
.then(res => res.json())
.then(data => {
  const container = document.createElement("div");
  container.className = "row content-grid";

  data.results.forEach(item => {
    const col = document.createElement("div");
    col.className = "col-card";
    col.innerHTML = `
      <div class="card-container card h-100 hover-shadow">
        <img src="${item.poster_url || '/static/images/no-poster.jpg'}" class="card-img-top" alt="${item.title}">
        <div class="card-body">
          <h6 class="card-title mb-1">${item.title.length > 20 ? item.title.slice(0, 20) + '…' : item.title}</h6>
          <p class="text-muted small">${item.release_date ? new Date(item.release_date).getFullYear() : 'N/A'} | ${item.type}</p>
          <a href="/content/${item.id}/" class="btn btn-outline-primary view-details w-100">Details</a>
        </div>
      </div>
    `;
    container.appendChild(col);
  });

  const recommendationsSection = document.querySelector(".container .mb-4");
  recommendationsSection.parentNode.insertBefore(container, recommendationsSection.nextSibling);
});

  
    function loadRecent(page = 1) {
      fetch(`/api/recent/?page=${page}`)
        .then((res) => res.json())
        .then((data) => {
          recentContainer.innerHTML = "";
          currentPage = page;
          const results = data.results || [];
          totalResults = data.count || 0;
          const pageSize = results.length || 10;
          totalPages = Math.ceil(totalResults / pageSize);
  
          results.forEach((item) => {
            const col = document.createElement("div");
            col.className = "col-card";
            col.innerHTML = `
              <div class="card-container card h-100 hover-shadow">
                <img src="${item.poster_url || '/static/images/no-poster.jpg'}" class="card-img-top" alt="${item.title}" onerror="this.src='/static/images/no-poster.jpg'">
                <div class="card-body">
                  <h6 class="card-title mb-1">${item.title.length > 20 ? item.title.slice(0, 20) + '…' : item.title}</h6>
                  <p class="text-muted small">${item.release_date ? new Date(item.release_date).getFullYear() : 'N/A'} | ${item.type}</p>
                  <a href="/content/${item.id}/" class="btn btn-outline-primary view-details w-100">Details</a>
                </div>
              </div>`;
            recentContainer.appendChild(col);
          });
  
          renderPagination();
        })
        .catch((error) => {
          console.error("Failed to fetch recent items:", error);
          recentContainer.innerHTML = `<div class="col-12 text-danger">⚠️ Could not load recent content</div>`;
        });
    }
  
    function renderPagination() {
      pagination.innerHTML = "";
      if (totalPages <= 1) return;
  
      const ul = document.createElement("ul");
      ul.className = "pagination justify-content-center";
  
      const addPage = (label, page, disabled = false, active = false) => {
        const li = document.createElement("li");
        li.className = `page-item ${disabled ? "disabled" : ""} ${active ? "active" : ""}`;
        const a = document.createElement("a");
        a.className = "page-link";
        a.href = "#";
        a.textContent = label;
        if (!disabled && !active) {
          a.addEventListener("click", (e) => {
            e.preventDefault();
            loadRecent(page);
            window.scrollTo({ top: 0, behavior: "smooth" });
          });
        }
        li.appendChild(a);
        ul.appendChild(li);
      };
  
      addPage("«", currentPage - 1, currentPage === 1);
  
      const start = Math.max(1, currentPage - 2);
      const end = Math.min(totalPages, currentPage + 2);
  
      if (start > 1) {
        addPage("1", 1);
        if (start > 2) {
          const ellipsis = document.createElement("li");
          ellipsis.className = "page-item disabled";
          ellipsis.innerHTML = `<span class="page-link">...</span>`;
          ul.appendChild(ellipsis);
        }
      }
  
      for (let i = start; i <= end; i++) {
        addPage(i, i, false, i === currentPage);
      }
  
      if (end < totalPages) {
        if (end < totalPages - 1) {
          const ellipsis = document.createElement("li");
          ellipsis.className = "page-item disabled";
          ellipsis.innerHTML = `<span class="page-link">...</span>`;
          ul.appendChild(ellipsis);
        }
        addPage(totalPages, totalPages);
      }
  
      addPage("»", currentPage + 1, currentPage === totalPages);
      pagination.appendChild(ul);
    }
  
    loadRecent();
  
  
  
    // === Популярні (без пагінації) ===
    const carouselInner = document.getElementById("popular-carousel-inner");

    function createPopularCard(item) {
        const col = document.createElement("div");
        col.className = "col-md-3";

        const card = document.createElement("div");
        card.className = "card-container card h-100 hover-shadow";

        const img = document.createElement("img");
        img.src = item.poster_url || "/static/images/no-poster.jpg";
        img.alt = item.title;
        img.className = "card-img-top";
        img.onerror = function () {
            this.src = "/static/images/no-poster.jpg";
        };

        const body = document.createElement("div");
        body.className = "card-body";

        const title = document.createElement("h5");
        title.className = "card-title";
        title.textContent = item.title.length > 30 ? item.title.slice(0, 30) + "…" : item.title;

        const info = document.createElement("p");
        info.className = "text-muted small mb-2";
        const year = item.release_date ? new Date(item.release_date).getFullYear() : "N/A";
        info.textContent = `${year} | ${item.type}`;

        const link = document.createElement("a");
        link.href = `/content/${item.id}/`;
        link.className = "btn btn-outline-primary view-details w-100";
        link.textContent = "View Details";

        body.appendChild(title);
        body.appendChild(info);
        body.appendChild(link);

        card.appendChild(img);
        card.appendChild(body);
        col.appendChild(card);
        return col;
    }

    function groupItems(items, perGroup = 4) {
        const groups = [];
        for (let i = 0; i < items.length; i += perGroup) {
            groups.push(items.slice(i, i + perGroup));
        }
        return groups;
    }

    fetch("/api/popular/")
        .then(res => {
            console.log("Popular API response status:", res.status);
            return res.json();
        })
        .then(data => {
            console.log("Popular data received:", data);
            console.log("Data length:", data ? data.length : 'undefined');
            // Популярний контент повертає прямий масив (без пагінації)
            const groups = groupItems(data, 4);
            groups.forEach((group, idx) => {
                const carouselItem = document.createElement("div");
                carouselItem.className = `carousel-item ${idx === 0 ? "active" : ""}`;

                const row = document.createElement("div");
                row.className = "row";

                group.forEach(item => {
                    row.appendChild(createPopularCard(item));
                });

                carouselItem.appendChild(row);
                carouselInner.appendChild(carouselItem);
            });
        })
        .catch(err => {
            console.error("Error loading popular content:", err);
            carouselInner.innerHTML = `<div class="text-center text-danger py-3">⚠️ Failed to load popular content</div>`;
        });
});
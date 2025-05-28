document.addEventListener('DOMContentLoaded', function () {
  const searchInput = document.getElementById('search');
  const searchDropdown = document.getElementById('search-results-dropdown');
  const searchResultsList = document.getElementById('search-results-list');
  const showAllResultsLink = document.getElementById('show-all-results-link');
  const searchForm = document.getElementById('global-search-form');
  const closeBtn = document.getElementById('close');
  const searchSubmit = document.getElementById('search-submit');

  if (!searchInput || !searchDropdown || !searchResultsList || !searchForm) return;

  // Debounce: обмеження запитів до API
  function debounce(func, wait) {
    let timeout;
    return function () {
      const context = this, args = arguments;
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        func.apply(context, args);
      }, wait);
    };
  }

  // Запит до API
  const fetchSearchResults = debounce(function (query) {
    if (query.length < 2) {
      searchDropdown.style.display = 'none';
      return;
    }

    fetch(`/api/search/autocomplete/?q=${encodeURIComponent(query)}`)
      .then(response => response.json())
      .then(data => {
        if (data.results && data.results.length > 0) {
          renderSearchResults(data.results);
          searchDropdown.style.display = 'block';
        } else {
          searchDropdown.style.display = 'none';
        }
      })
      .catch(error => {
        console.error('Error fetching search results:', error);
        searchDropdown.style.display = 'none';
      });
  }, 300);

  // Відображення результатів
  function renderSearchResults(results) {
    searchResultsList.innerHTML = '';

    results.forEach(result => {
      const item = document.createElement('div');
      item.className = 'search-result-item';

      const poster = result.poster_url
        ? `<img src="${result.poster_url}" alt="${result.title}" onerror="this.style.display='none'">`
        : `<div class="no-poster"><i class="fa fa-film"></i></div>`;

      item.innerHTML = `
        ${poster}
        <div class="search-result-info">
          <div class="search-result-title">${result.title}</div>
          <div class="search-result-type">${result.type}</div>
        </div>
      `;

      item.addEventListener('click', () => {
        window.location.href = result.url;
      });

      searchResultsList.appendChild(item);
    });

    if (showAllResultsLink) {
      showAllResultsLink.href = `/search/?q=${encodeURIComponent(searchInput.value)}`;
    }
  }

  // Події
  searchInput.addEventListener('input', function () {
    fetchSearchResults(this.value);
  });

  searchInput.addEventListener('focus', function () {
    if (this.value.length >= 2 && searchResultsList.children.length > 0) {
      searchDropdown.style.display = 'block';
    }
  });

  document.addEventListener('click', function (e) {
    if (!e.target.closest('.search-container')) {
      searchDropdown.style.display = 'none';
    }
  });

  if (closeBtn) {
    closeBtn.addEventListener('click', function (e) {
      e.preventDefault();
      searchInput.value = '';
      searchDropdown.style.display = 'none';
      searchInput.focus();
    });
  }

  if (showAllResultsLink) {
    showAllResultsLink.addEventListener('click', function (e) {
      e.preventDefault();
      const query = searchInput.value.trim();
      if (query.length > 0) {
        searchForm.submit();
      } else {
        searchInput.focus();
      }
    });
  }

  if (searchSubmit) {
    searchSubmit.addEventListener('click', function (e) {
      e.preventDefault();
      const query = searchInput.value.trim();
      if (query.length > 0) {
        searchForm.submit();
      }
    });
  }

  searchInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      const query = searchInput.value.trim();
      if (query.length > 0) {
        searchForm.submit();
      }
    }
  });
});

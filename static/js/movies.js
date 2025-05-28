document.addEventListener('DOMContentLoaded', function() {
    const moviesGrid = document.getElementById('movies-grid');
    const loadMoreBtn = document.getElementById('load-more');
    const loadingSpinner = document.getElementById('loading-spinner');

    const genreFilter = document.getElementById('genre-filter');
    const yearFilter = document.getElementById('year-filter');
    const ratingFilter = document.getElementById('rating-filter');

    let currentPage = 1;
    let isLoading = false;
    let hasMore = true;

    let currentFilters = {
        genre: '',
        year: '',
        rating: ''
    };
    let totalPages = 1;
    let totalResults = 0;

    const paginationContainer = document.createElement('div');
    paginationContainer.className = 'pagination-container mt-4';
    paginationContainer.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <div class="results-info">
                <span id="results-count" class="text-muted">Loading...</span>
            </div>
        </div>
        <nav aria-label="Movie pagination">
            <ul id="pagination" class="pagination justify-content-center"></ul>
        </nav>
    `;
    moviesGrid.parentNode.insertBefore(paginationContainer, loadMoreBtn.parentNode);

    loadMovies();

    [genreFilter, yearFilter, ratingFilter].forEach(filter => {
        if (filter) {
            filter.addEventListener('change', function() {
                currentFilters[this.id.replace('-filter', '')] = this.value;
                resetPagination();
                loadMovies();
            });
        }
    });

    function resetPagination() {
        currentPage = 1;
        moviesGrid.innerHTML = '';
        hasMore = true;
        totalPages = 1;
        totalResults = 0;
    }

    function loadMovies() {
        if (isLoading) return;

        isLoading = true;
        loadMoreBtn.style.display = 'none';
        loadingSpinner.style.display = 'block';

        const params = new URLSearchParams({
            page: currentPage,
            genre: currentFilters.genre,
            year: currentFilters.year,
            min_rating: currentFilters.rating
        });

        fetch(`/api/movies/?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                moviesGrid.innerHTML = '';

                if (data.movies && data.movies.length > 0) {
                    renderMovies(data.movies);
                    totalPages = data.total_pages || Math.ceil((data.count || data.movies.length) / 20);
                    totalResults = data.count || data.movies.length;
                    hasMore = currentPage < totalPages;
                } else {
                    hasMore = false;
                    totalPages = 1;
                    totalResults = 0;
                    moviesGrid.innerHTML = `
                        <div class="col-12 text-center py-5">
                            <h4>No movies found</h4>
                            <p>Try adjusting your search or filters</p>
                        </div>
                    `;
                }

                updatePagination();
                updateResultsInfo();
            })
            .catch(error => {
                console.error('Error loading movies:', error);
                moviesGrid.innerHTML = `
                    <div class="col-12 text-center py-5 text-danger">
                        <h4>Error loading movies</h4>
                        <p>Please try again later</p>
                    </div>
                `;
                updateResultsInfo();
            })
            .finally(() => {
                isLoading = false;
                loadingSpinner.style.display = 'none';
            });
    }

    function updatePagination() {
        const paginationElement = document.getElementById('pagination');
        paginationElement.innerHTML = '';

        if (totalPages <= 1) return;

        const prevItem = document.createElement('li');
        prevItem.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
        prevItem.innerHTML = `<a class="page-link" href="#" data-page="${currentPage - 1}"><i class="bi bi-chevron-left"></i></a>`;
        paginationElement.appendChild(prevItem);

        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);

        if (startPage > 1) {
            const firstItem = document.createElement('li');
            firstItem.className = 'page-item';
            firstItem.innerHTML = '<a class="page-link" href="#" data-page="1">1</a>';
            paginationElement.appendChild(firstItem);

            if (startPage > 2) {
                const ellipsisItem = document.createElement('li');
                ellipsisItem.className = 'page-item disabled';
                ellipsisItem.innerHTML = '<span class="page-link">...</span>';
                paginationElement.appendChild(ellipsisItem);
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            const pageItem = document.createElement('li');
            pageItem.className = `page-item ${i === currentPage ? 'active' : ''}`;
            pageItem.innerHTML = `<a class="page-link" href="#" data-page="${i}">${i}</a>`;
            paginationElement.appendChild(pageItem);
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                const ellipsisItem = document.createElement('li');
                ellipsisItem.className = 'page-item disabled';
                ellipsisItem.innerHTML = '<span class="page-link">...</span>';
                paginationElement.appendChild(ellipsisItem);
            }

            const lastItem = document.createElement('li');
            lastItem.className = 'page-item';
            lastItem.innerHTML = `<a class="page-link" href="#" data-page="${totalPages}">${totalPages}</a>`;
            paginationElement.appendChild(lastItem);
        }

        const nextItem = document.createElement('li');
        nextItem.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
        nextItem.innerHTML = `<a class="page-link" href="#" data-page="${currentPage + 1}"><i class="bi bi-chevron-right"></i></a>`;
        paginationElement.appendChild(nextItem);

        paginationElement.querySelectorAll('a.page-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const page = parseInt(this.getAttribute('data-page'));
                if (page && page !== currentPage && page >= 1 && page <= totalPages) {
                    currentPage = page;
                    loadMovies();
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }
            });
        });
    }

    function updateResultsInfo() {
        const resultsCount = document.getElementById('results-count');
        if (totalResults > 0) {
            const startItem = (currentPage - 1) * 20 + 1;
            const endItem = Math.min(currentPage * 20, totalResults);
            resultsCount.textContent = `Showing ${startItem}-${endItem} of ${totalResults} results (Page ${currentPage} of ${totalPages})`;
        } else {
            resultsCount.textContent = 'No results found';
        }
    }

    function renderMovies(movies) {
        movies.forEach(movie => {
            const movieCol = document.createElement('div');
            movieCol.className = 'col-6 col-sm-4 col-md-3 col-lg-2 mb-4';
            movieCol.innerHTML = `
                <div class="card-container card h-100 hover-shadow">
                    <img 
                        src="${movie.poster_url || '/static/images/no-poster.jpg'}" 
                        alt="${movie.title} poster" 
                        class="card-img-top img-fluid" 
                        style="height: 200px; object-fit: cover" 
                        onerror="this.onerror=null; this.src='/static/images/no-poster.jpg'"
                        >

                    <div class="card-body">
                        <h6 class="card-title mb-1">${movie.title.length > 20 ? movie.title.substring(0, 20) + '...' : movie.title}</h6>
                        <div class="d-flex justify-content-between align-items-center small text-muted mb-2">
                            <span class="badge bg-primary">Movie</span>
                            <span>${movie.release_date ? new Date(movie.release_date).getFullYear() : 'N/A'}</span>
                        </div>
                        <div class="d-flex justify-content-between small text-muted">
                            ${movie.rating ? `<span><i class="bi bi-star-fill text-warning"></i> ${parseFloat(movie.rating).toFixed(1)}</span>` : ''}
                            ${movie.runtime ? `<span>${Math.floor(movie.runtime/60)}h ${movie.runtime%60}m</span>` : ''}
                        </div>
                        <div class="mt-2">
                            <a href="/content/${movie.id}/" class="btn btn-sm btn-outline-primary w-100">View Details</a>
                        </div>
                    </div>
                </div>
            `;
            moviesGrid.appendChild(movieCol);
        });
    }
});

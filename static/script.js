/* Vars */

const HeaderIconContainer = document.getElementById("header-icon-container")
const searchBtn = document.getElementById("searchBtn");
const searchBtnImg = document.getElementById("searchBtnImg");
const searchBtnContainer = document.querySelector(".searchBtn-container");
const SearchInput = document.getElementById("searchInput");
const musicsContainer = document.getElementById("musicsContainer");


let maxLength = 40;
const productDescs = document.querySelectorAll(".productDesc");
const urlParams = new URLSearchParams(window.location.search);
const queryParam = urlParams.get('q');


let debounceTimer;


/* Functions */ 

function renderVideos(videos) {
    if (!videos || videos.length === 0) {
        musicsContainer.innerHTML = "<p>Aucun résultat trouvé /:</p>";
        return;
    }

    const htmlContent = videos.map(video => {
        const description = `${video.title} | ${video.channel || 'Artiste inconnue'}`;

        return `
            <li class="musicsRollers" data-id="${video.id}">
                <img class="productRollBack" src="${video.thumbnail}" alt="${video.title}">
                <div class="productTitle">
                    <p class="productDesc" title="${description}">${description}</p>
                </div>
            </li>
        `;
    }).join('');

    musicsContainer.innerHTML = htmlContent;
}

async function callBackEnd(query) {
    if (!query) return;

    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        if (data.videos) {
            renderVideos(data.videos); 
        }
    } catch(error) {
        console.error("Error at backend:", error);
    }
}




const videoId = urlParams.get('id');

if (videoId) {
    loadAndPlayTrack(videoId);
}


/* Events */

window.addEventListener('popstate', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('q');
    if (query) {
        searchInput.value = query;
        callBackEnd(query);
    } else {
        searchInput.value = '';
    }
});

searchBtn.addEventListener("click", () => {
    searchBtnContainer.classList.toggle("open");
    SearchInput.classList.toggle("open");

    if (searchBtnContainer.classList.contains("open")) {
        searchBtnImg.src = "../images/backsearchcontainer.png";
    } else {
        searchBtnImg.src = "../images/searchBtnImg.png";
    }
});

HeaderIconContainer.addEventListener("click", () => {
    window.location.assign("/");
});

musicsContainer.addEventListener('click', (event) => {
    const card = event.target.closest('.musicsRollers');
    if (card) {
        const videoId = card.getAttribute('data-id');
        window.location.assign(`/listen?id=${videoId}`);
    }
});

SearchInput.addEventListener("input", () => {
    const currentSearch = SearchInput.value.trim();
    clearTimeout(debounceTimer);
    if (window.location.pathname !== "/" && window.location.pathname !== "/search") {
        if (currentSearch) {
            window.location.assign(`/search?q=${encodeURIComponent(currentSearch)}`);
        }
        return;
    }

    if (currentSearch) {
        window.history.replaceState(null, "", `/search?q=${encodeURIComponent(currentSearch)}`);
        debounceTimer = setTimeout(() => {
            callBackEnd(currentSearch);
        }, 300);
    } else {
        window.history.replaceState(null, "", "/");
        if (musicsContainer) musicsContainer.innerHTML = "";
    }
});


/* Conds */

/* Conds vars */


/* Product */

productDescs.forEach((desc) => {
    const originalText = desc.textContent.trim();
    
    if (originalText.length > maxLength) {
        desc.textContent = originalText.slice(0, maxLength) + "...";
    }
});


/* Title */

maxLength = 40;




if (queryParam) {
    SearchInput.value = queryParam;
    SearchInput.classList.add("open");
    searchBtnContainer.classList.add("open");

    searchBtnImg.src = "/images/backsearchcontainer.png";
    callBackEnd(queryParam);
}
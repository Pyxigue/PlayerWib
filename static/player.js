/* Vars */
const HeaderIconContainer = document.getElementById("header-icon-container")
const searchBtn = document.getElementById("searchBtn");
const searchBtnImg = document.getElementById("searchBtnImg");
const searchBtnContainer = document.querySelector(".searchBtn-container");
const SearchInput = document.getElementById("searchInput");
const musicsContainer = document.getElementById("musicsContainer");
const audioPlayer = document.getElementById("AudioPlayer");
const currentTitle = document.getElementById("currentTitle");
const currentArtist = document.getElementById("currentArtist");
const currentThumbnail = document.getElementById("currentThumbnail");
const PauseBtn = document.getElementById("PauseBtn");
const PauseImg = document.getElementById("PauseImg");

const progressRange = document.getElementById("progress-range");
const currentTimeEl = document.getElementById("current-time");
const endTimeEl = document.getElementById("end-time");

const volumeContainer = document.querySelector(".volume-container");
const volumeIndicatorContainer = document.getElementById("VolumeControlInput");


const rewindBtn = document.getElementById("Backtensecs");
const forwardBtn = document.getElementById("Forwardtensecs");



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


async function loadAndPlayTrack(videoId) {
    if (!videoId || !audioPlayer) return;
    if (progressRange) progressRange.value = 0;
    try {
    currentThumbnail.classList.remove("paused");
    currentThumbnail.classList.add("loading");

    if (currentTimeEl) currentTimeEl.textContent = "00:00";
    if (endTimeEl) endTimeEl.textContent = "00:00";
    if (progressRange) progressRange.value = 0;

    if (currentTitle) currentTitle.textContent = "Chargement...";

    const response = await fetch('/api/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: videoId })
    });

    const data = await response.json();

    if (data.status === 'success') {
        if (currentTitle) currentTitle.textContent = data.title;
        if (currentArtist) currentArtist.textContent = data.channel;
        if (currentThumbnail && data.thumbnail) currentThumbnail.src = data.thumbnail;

        audioPlayer.src = data.stream_url;

        await audioPlayer.play();

        currentThumbnail.classList.remove("loading");
        currentThumbnail.classList.remove("paused")
        if (PauseImg) PauseImg.src = "/images/pause.png";
        if (PauseBtn) PauseBtn.classList.remove("brillant");

    } else {
        currentThumbnail.classList.remove("loading");
        currentThumbnail.classList.add("paused");
    }

    } catch (error) {
    console.error("Error :", error);
    currentThumbnail.classList.remove("loading");
    currentThumbnail.classList.add("paused");

    if (PauseBtn) PauseBtn.classList.add("brillant");
    }
}


const videoId = urlParams.get('id');

if (videoId) {
    loadAndPlayTrack(videoId);
}


function formatTime(seconds) {
  if (isNaN(seconds) || seconds < 0) return "00:00";
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  const formattedMinutes = String(minutes).padStart(2, '0');
  const formattedSeconds = String(remainingSeconds).padStart(2, '0');
  return `${formattedMinutes}:${formattedSeconds}`;
}

/* Events */

window.addEventListener("DOMContentLoaded", async () => {
    try {
        await audioPlayer.play(); 

        currentThumbnail.classList.remove("paused");
        if (PauseImg) PauseImg.src = "/images/pause.png";
        if (PauseBtn) PauseBtn.classList.remove("brillant");
        
    } catch (error) {
        console.warn("Failed to autoplay, please click manually on the play button;", error);
        if (PauseBtn) PauseBtn.classList.add("brillant");
        if (currentThumbnail) currentThumbnail.classList.add("paused");
    }
});


window.addEventListener('popstate', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('q');
    if (query && SearchInput) {
        SearchInput.value = query;
        callBackEnd(query);
    } else if (SearchInput) {
        SearchInput.value = '';
    }
    });


audioPlayer.addEventListener("ended", () => {
    if (PauseImg) PauseImg.src = "/images/play.png";
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


progressRange.addEventListener("input", () => {
  if (audioPlayer.duration) {
    const seekTime = (progressRange.value / 100) * audioPlayer.duration;
    audioPlayer.currentTime = seekTime;
  }
});


rewindBtn.addEventListener("click", () => {
  if (audioPlayer) {
    audioPlayer.currentTime = Math.max(0, audioPlayer.currentTime - 10);
  }
});

forwardBtn.addEventListener("click", () => {
  if (audioPlayer) {
    audioPlayer.currentTime = Math.min(audioPlayer.duration || 0, audioPlayer.currentTime + 10);
  }
});



PauseBtn.addEventListener("click", async () => {
    PauseBtn.classList.remove("brillant");
    if (audioPlayer.paused) {
    audioPlayer.play();
    PauseImg.src= "/images/pause.png"
    currentThumbnail.classList.remove("paused")
    } else {
    audioPlayer.pause();
    PauseImg.src = "/images/play.png";
    currentThumbnail.classList.add("paused")
    }
});


AudioPlayer.addEventListener("ended", () => {
    PauseImg.src = "/images/play.png";
    currentThumbnail.classList.add("paused");
});


productDescs.forEach((desc) => {
    const originalText = desc.textContent.trim();
    
    if (originalText.length > maxLength) {
        desc.textContent = originalText.slice(0, maxLength) + "...";
    }
});


const loopBtn = document.getElementById("playagainBtn");


loopBtn.addEventListener("click", () => {
    if (!audioPlayer) return; 

    audioPlayer.loop = !audioPlayer.loop;

    if (audioPlayer.loop) {
        loopBtn.classList.add("active"); 
    } else {
        loopBtn.classList.remove("active");
    }
});

/* Title */

maxLength = 40;


const originalTextCurrentTitle = currentTitle.textContent.trim();

if (originalTextCurrentTitle.length > maxLength) {
    currentTitle.textContent = originalTextCurrentTitle.slice(0, maxLength) + "...";
}

/* Artist */

const originalTextCurrentArtist = currentArtist.textContent.trim();

if (originalTextCurrentArtist.length > maxLength) {
    currentArtist.textContent = originalTextCurrentArtist.slice(0, maxLength) + "...";
}



if (queryParam) {
    SearchInput.value = queryParam;
    SearchInput.classList.add("open");
    searchBtnContainer.classList.add("open");

    searchBtnImg.src = "/images/backsearchcontainer.png";
    callBackEnd(queryParam);
}

if (!audioPlayer.play) {
    currentThumbnail.classList.add("paused");
} else {
    currentThumbnail.classList.remove("paused");
}

audioPlayer.addEventListener("timeupdate", () => {
  if (audioPlayer.duration && progressRange) {
    const progressPercent = (audioPlayer.currentTime / audioPlayer.duration) * 100;
    progressRange.value = progressPercent;
  }
});


/* Timeline*/


audioPlayer.addEventListener("timeupdate", () => {
    if (currentTimeEl) {
        currentTimeEl.textContent = formatTime(audioPlayer.currentTime);
    }

    if (audioPlayer.duration && progressRange) {
        const progressPercent = (audioPlayer.currentTime / audioPlayer.duration) * 100;
        progressRange.value = progressPercent;
    }
});


audioPlayer.addEventListener("loadedmetadata", () => {
    if (endTimeEl) {
        endTimeEl.textContent = formatTime(audioPlayer.duration);
    }
});

progressRange.addEventListener("input", () => {
    if (audioPlayer.duration) {
        const seekTime = (progressRange.value / 100) * audioPlayer.duration;
        audioPlayer.currentTime = seekTime;

        if (currentTimeEl) {
            currentTimeEl.textContent = formatTime(seekTime);
        }
    }
});


volumeContainer.addEventListener("mousemove", () => {
    volumeIndicatorContainer.classList.add("active");
});

volumeContainer.addEventListener("mouseleave", () => {
    volumeIndicatorContainer.classList.remove("active");
});
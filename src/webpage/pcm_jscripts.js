var woj_labs = ['Dolnośląskie', 'Kujawsko-pomorskie', 'Lubelskie', 'Lubuskie', 'Łódzkie', 'Małopolskie', 'Mazowieckie',
'Opolskie', 'Podkarpackie', 'Podlaskie', 'Pomorskie', 'Śląskie', 'Świętokrzyskie', 'Warmińsko-mazurskie',
'Wielkopolskie', 'Zachodniopomorskie'];

function initMap() {

    // Tworzymy obiekt mapy
    var map = L.map('map').setView([52.2298, 21.0117], 10);
    var drop = document.getElementById("drop1");

    // Dodajemy mape
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 20,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    // Linijka, ktora powoduje, że przy zoomowaniu przy pomocy przycisków nie znika menu
    map.getContainer().focus = ()=>{}

    // Wypełniamy menu odpowiednimi labelami
    for(i = 0; i < woj_labs.length; i++){
    	    var el = document.createElement("a");
    	    var url = woj_labs[i];
    	    el.id = i.toString();
    	    el.href = "javascript:undefined;";
    	    el.setAttribute("onclick", "javascript:toggle(this.id);");
    	    el.setAttribute("style", "outline: none; border-color: transparent;");
    	    el.innerHTML = "<b>" + url + "</b>";
    	    drop.appendChild(el);
    }
}
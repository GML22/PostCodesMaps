// Deklaracja podstawowych zmiennych globalnych
var woj_labs = ['dolnośląskie', 'kujawsko-pomorskie', 'lubelskie', 'lubuskie', 'łódzkie', 'małopolskie', 'mazowieckie',
'opolskie', 'podkarpackie', 'podlaskie', 'pomorskie', 'śląskie', 'świętokrzyskie', 'warmińsko-mazurskie',
'wielkopolskie', 'zachodniopomorskie'];
var woj_files = ['02_DOLNOSLASKIE', '04_KUJAWSKO-POMORSKIE', '06_LUBELSKIE', '08_LUBUSKIE', '10_LODZKIE',
'12_MALOPOLSKIE', '14_MAZOWIECKIE', '16_OPOLSKIE', '18_PODKARPACKIE', '20_PODLASKIE', '22_POMORSKIE', '24_SLASKIE',
 '26_SWIETOKRZYSKIE', '28_WARMINSKO-MAZURSKIE', '30_WIELKOPOLSKIE', '32_ZACHODNIOPOMORSKIE'];
var woj_len = woj_labs.length;
var woj_colors = ['#3cb44b', '#46f0f0', '#4363d8', '#f58231', '#000075', '#911eb4', '#ffd700', '#f032e6', '#bcf60c',
'#ffffff', '#ffff54', '#e6beff', '#ffa07a', '#fffac8', '#c71585', '#aaffc3'];
var font_colors = ['#ffffff', '#000000', '#ffffff', '#ffffff', '#ffffff', '#ffffff', '#000000', '#ffffff', '#000000',
'#000000', '#000000', '#000000', '#000000', '#000000', '#ffffff', '#000000']
var woj_visib = [];
var map_lays = new Array(woj_len);
var map;

function initMap() {
    // Funkcja generujaca glowna mape oraz uzupelniajaca menu

    // Tworzymy obiekt mapy
    var drop = document.getElementById("drop1");
    map = L.map('map').setView([52.2298, 21.0117], 6);

    // Dodajemy mape
    L.tileLayer('http://{s}.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}', {
        maxZoom: 20,
        subdomains:['mt0','mt1','mt2','mt3']
    }).addTo(map);

    // Linijka, ktora powoduje, że przy zoomowaniu przy pomocy przycisków nie znika menu
    map.getContainer().focus = ()=>{}

    // Wypełniamy menu odpowiednimi labelami
    for(i = 0; i < woj_len; i++){
        // Dodajemy do wektora informacje, że dana wartswa nie jest w tym momencie widoczna
        woj_visib.push(false);

        // Uzupeniamy menu nazwami województw
    	var el = document.createElement("a");
        el.id = i.toString();
        el.href = "javascript:undefined;";
        el.setAttribute("onclick", "javascript:disp_layer(this.id);");
        el.setAttribute("style", "outline: none; border-color: transparent;");
        el.innerHTML = "<b>" + 'Województwo ' + woj_labs[i] + "</b>";
        drop.appendChild(el);
    }
};

function disp_layer(num){
    // Funkcja wyświetlająca warstwy kodow pocztowych dla województw

    // Deklaracja podstawowych zmiennych
    var curr_col = woj_colors[num]
    var curr_lay_name = woj_files[num]
    var fin_lay_path = "./fin_maps/" + curr_lay_name + "/" + curr_lay_name + "_ALL_PC_4326.geojson"

    // Jezeli warstwa danego wojewodztwa nie jest juz widoczna to ja wczytujemy
	if(!woj_visib[num]){
	    // Zmieniamy kolor wojewodztwa w menu
        document.getElementById(num).style.backgroundColor = curr_col;
        document.getElementById(num).style.color = font_colors[num];

        // Tworzymy warstwe geojson i dodajemy ja do mapy
        var geojsonLayer = new L.GeoJSON.AJAX(fin_lay_path, {style: {weight: 5, opacity: 1.0, color: curr_col},
        onEachFeature: function p(feature, layer) {layer.bindPopup("<b>Kod pocztwy: " + feature.properties.Name +
        "</b>");}});
        geojsonLayer.on('data:loaded', function() {map.fitBounds(geojsonLayer.getBounds())});
        geojsonLayer.addTo(map);

        // Zapisujemy warstwe geojson w macierzy wartsw
        map_lays[num] = geojsonLayer;

        // Uzupelniamy wektor widocznosci
        woj_visib[num] = true;
    }else{
        // Przywracamy pierwotny kolor przycisku w menu
        document.getElementById(num).style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
        document.getElementById(num).style.color = '#ffffff';

        // Usuwamy z mapy dana warstwe wojewodztwa
        map.removeLayer(map_lays[num]);

        // Uzupelniamy wektor widocznosci
        woj_visib[num] = false;
    }
};
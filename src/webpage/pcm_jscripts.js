// Deklaracja podstawowych zmiennych globalnych
var woj_labs = ['dolnośląskie', 'kujawsko-pomorskie', 'lubelskie', 'lubuskie', 'łódzkie', 'małopolskie', 'mazowieckie',
'opolskie', 'podkarpackie', 'podlaskie', 'pomorskie', 'śląskie', 'świętokrzyskie', 'warmińsko-mazurskie',
'wielkopolskie', 'zachodniopomorskie'];
var woj_files = ['02_DOLNOSLASKIE', '04_KUJAWSKO-POMORSKIE', '06_LUBELSKIE', '08_LUBUSKIE', '10_LODZKIE',
'12_MALOPOLSKIE', '14_MAZOWIECKIE', '16_OPOLSKIE', '18_PODKARPACKIE', '20_PODLASKIE', '22_POMORSKIE', '24_SLASKIE',
 '26_SWIETOKRZYSKIE', '28_WARMINSKO-MAZURSKIE', '30_WIELKOPOLSKIE', '32_ZACHODNIOPOMORSKIE'];
var woj_len = woj_labs.length;
var woj_colors = ['#3cb44b', '#46f0f0', '#4363d8', '#800000', '#000075', '#911eb4', '#ffd700', '#f032e6', '#bcf60c',
'#ffffff', '#ffff54', '#e6beff', '#ffa07a', '#fffac8', '#c71585', '#aaffc3'];
var font_colors = ['#ffffff', '#000000', '#ffffff', '#ffffff', '#ffffff', '#ffffff', '#000000', '#ffffff', '#000000',
'#000000', '#000000', '#000000', '#000000', '#000000', '#ffffff', '#000000'];
var woj_visib = [];
var map_lays = new Array(woj_len);
var pc_codes = [];
var visib_pc = [];
var autofill_dict = {};
var gmn_pow_nms_dict;
var pl_names_dict;
var pc_nums_dict = {};
var gmn_pow_keys;
var map;

function initMap(){
    // Funkcja generujaca glowna mape oraz uzupelniajaca menu

    // Tworzymy obiekt mapy
    var drop = document.getElementById("drop1");
    var base_path = "./files/POSTCODES_TXT/";

    map = L.map('map').setView([52.2298, 21.0117], 6);

    // Dodajemy mape
    L.tileLayer('http://{s}.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}', {
        maxZoom: 20,
        subdomains:['mt0','mt1','mt2','mt3']
    }).addTo(map);

    // Linijka, ktora powoduje, że przy zoomowaniu przy pomocy przycisków nie znika menu
    map.getContainer().focus = ()=>{};

    // Wypełniamy menu odpowiednimi labelami
    for(var i = 0; i < woj_len; i++){
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

    // Dodajemy czyszczenie autosugestii po kliknieciu przycisku czyszczacego
    $('input[type=search]').on('search', function () {
        clear_not_vis_lys();
    });

    // Wczytujemy niezbędne słowniki
    $.get({url: base_path + "GMN_POW_NMS.txt", success: function(data){
        gmn_pow_nms_dict = JSON.parse(data);
        }, async: false});
    $.get({url: base_path + "PL_NAMES.txt", success: function(data){pl_names_dict = JSON.parse(data); }, async: false});

    gmn_pow_keys = Object.keys(gmn_pow_nms_dict);
};

function disp_layer(num){
    // Funkcja wyświetlająca warstwy kodow pocztowych dla województw

    // Deklaracja podstawowych zmiennych
    var curr_col = woj_colors[num];
    var curr_lay_name = woj_files[num];
    var fin_lay_path = "./fin_maps/" + curr_lay_name + "/" + curr_lay_name + "_ALL_PC_4326.geojson";

    // Jezeli warstwa danego wojewodztwa nie jest juz widoczna to ja wczytujemy
	if(!woj_visib[num]){
	    // Zmieniamy kolor wojewodztwa w menu
        document.getElementById(num).style.backgroundColor = curr_col;
        document.getElementById(num).style.color = font_colors[num];

        // Tworzymy warstwe geojson i dodajemy ja do mapy
        var geojsonLayer = new L.GeoJSON.AJAX(fin_lay_path, {style: {weight: 5, opacity: 1.0, color: curr_col},
            onEachFeature: function p(feature, layer) {
                layer.bindPopup(L.popup({"autoClose": false, "closeOnClick": null}).setContent("<b>Kod pocztowy:</b> " +
                feature.properties.Name + "<br><b>Nazwa gminy:</b> " + pl_names_dict[feature.properties.Gmina] +
                "<br><b>Liczba punktów adresowych:</b> " + feature.properties.PC_NUM));
                 layer.on('contextmenu', function (e){
                    if(woj_visib[num]){
                        layer.bindTooltip("<b>" + feature.properties.Name + "</b>", {permanent: true,
                            direction: "center", className: 'tltip_stl'});
                }
             });
        }});

        // Przesuwamy mape do wczytanej warstwy
        geojsonLayer.on('data:loaded', function(){
            if(map.getZoom() < 15){
                map.fitBounds(geojsonLayer.getBounds());
            }
        });
        geojsonLayer.addTo(map);

        // Zapisujemy warstwe geojson w macierzy wartsw
        map_lays[num] = geojsonLayer;

        // Uzupelniamy wektor widocznosci
        woj_visib[num] = true;
    }else{
        // Przywracamy pierwotny kolor przycisku w menu
        document.getElementById(num).style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
        document.getElementById(num).style.color = '#FFFFFF';

        // Usuwamy z mapy dana warstwe wojewodztwa
        map.removeLayer(map_lays[num]);

        // Uzupelniamy wektor widocznosci
        woj_visib[num] = false;
    }
};

function key_down_handler(event){
    // Funkcja obslugujaca wyszukiwarke

    var c_key = event.key;
    var parent_node = event.target;
    var p_txt = parent_node.value;
    var base_path = "./files/POSTCODES_TXT/";
    var auto_cmpl = document.getElementById('autoc1');
    var c_txt;
    var c_file_path;
    var pc_dict;

    if (c_key !== "Backspace"){
        c_txt = p_txt + c_key;
    } else{
        c_txt = p_txt.substring(0, p_txt.length - 1);
    }

    if (c_txt.match("^[0-9]{1,2}$|^[0-9]{2}-[0-9]{0,3}$") != null){
        // Ustalamy link do pliku z kodami pocztowymi
        if (c_txt.length == 1){
            c_file_path = base_path + "PC_" + c_txt +  "0.txt";
        } else{
            c_file_path = base_path + "PC_" + c_txt.substring(0, 2) +  ".txt";
        }

        // Wczytujemy odpowiedni plik .txt z kodami pocztowymi
        $.get({url: c_file_path, success: function(data){pc_dict = JSON.parse(data);}, async: false});

        // Wybieramy pierwszych 'n' pasujacych kodow pocztowych i zapisujemy je do slownika autofill
        var pc_dict_keys = Object.keys(pc_dict);

        // Czyścimy dotychczasowe obiekty na liście autocomplete
        clear_not_vis_lys();
        pc_nums_dict = {}
        var count = 0;

        for(var i = 0; i < pc_dict_keys.length; i++){

            var c_pc_gmn = pc_dict_keys[i];
            var c_pc = c_pc_gmn.slice(0, c_pc_gmn.indexOf("_"))

            if (pc_dict_keys[i].startsWith(c_txt) && count <= 10 && !(c_pc_gmn in autofill_dict)){
                // Słownik parametrow ksztaltu
                plg_list = pc_dict[c_pc_gmn];

                // Wyznaczamy finalna nazwe gminy
                gmn_name = plg_list[0]["Gmina"];

                // Przypisujemy do słowników finalny wielokat i liczbę punktow adresowych
                var fin_polys_list = [];
                var fin_nums_list = [];

                 for(var j = 0; j < plg_list.length; j++){
                    fin_polys_list.push(plg_list[j]["Polygon"]);
                    fin_nums_list.push(plg_list[j]["PC_NUM"]);
                }

                autofill_dict[c_pc_gmn] = fin_polys_list;
                pc_nums_dict[c_pc_gmn] = fin_nums_list;

                // Uzupełniamy liste autosugestii
                if (visib_pc.indexOf(c_pc_gmn) < 0){
                    inn_txt = "&nbsp; &nbsp;<strong>&#x293F; " + c_txt + "</strong>" +
                        c_pc.substring(c_txt.length, c_pc.length) + " (gm. " + pl_names_dict[gmn_name] + ")";
                }else{
                    inn_txt = "<strong>&nbsp; &nbsp;&#9989; " + c_txt + c_pc.substring(c_txt.length, c_pc.length) +
                        " (gm. " + pl_names_dict[gmn_name] + ")</strong>";
                }

                // Parametryzujemy nowy element i dodajemy go jako autosugestie
                inn_val = c_pc + " (gm. " + pl_names_dict[gmn_name] + ")";
                b = document.createElement("DIV");
                b.setAttribute("class", "ac_butt");
                b.href = "javascript:undefined;";
                b.setAttribute("id", c_pc_gmn);
                b.innerHTML = inn_txt;
                b.value = inn_val;
                b.setAttribute("onclick", "javascript:disp_pc(this.id, this.value);");
                auto_cmpl.appendChild(b);
                count++;
            }
        }
    } else{
        // Czyścimy dotychczasowe obiekty na liście autocomplete
        clear_not_vis_lys();
    }
};

function disp_pc(pc_code, str_val){
    var gmn_name = str_val.slice(str_val.indexOf("gm.") + 4, str_val.length - 1);
    var geojson_list = autofill_dict[pc_code];
    var pc_nums_list = pc_nums_dict[pc_code]
    var geojsons_group = new L.FeatureGroup();
    var pc_inds = visib_pc.indexOf(pc_code);
    var c_autof = document.getElementById(pc_code);
    var c_autof_val = c_autof.value;
    var p_autof_val = c_autof.innerHTML;
    var search_val = document.getElementById('searchInput').value;
    var c_pc = pc_code.slice(0, pc_code.indexOf("_"))

    if(pc_inds < 0){
        // Parsujemy WKT kazdego wielokata z listy i dodajemy go do grupy warstw (layerGroup)
        for(var i = 0; i < geojson_list.length; i++){
            // Tworzymy warstwę
            geojsonLayer =  omnivore.wkt.parse(geojson_list[i]);

            // Zmianiemy styl warstwy
            geojsonLayer.eachLayer(function (layer){
                layer.setStyle({color: "#FF6600", weight: 5, opacity: 1.0});
                layer.bindPopup(L.popup({"autoClose": false, "closeOnClick": null}).setContent("<b>Kod pocztowy:</b> " +
                c_pc + "<br><b>Gmina:</b> " + gmn_name + "<br><b>Liczba punktów adresowych:</b> " + pc_nums_list[i]));
                layer.bindTooltip("<b>" + c_pc + "</b>", {permanent: true, direction: "center",className: 'tltip_stl'});
            });

            // Dodajemy biezaca warstwe do grupy
            geojsons_group.addLayer(geojsonLayer);
        }

        // Przesuwamy mapę do współrzędnych grupy
        geojsons_group.addTo(map);
        pc_codes.push(geojsons_group);
        map.fitBounds(geojsons_group.getBounds());
        visib_pc.push(pc_code);

        // Zmieniamy kolor przycisku czyszczenia
        document.getElementById('clr_btn').style.backgroundColor = 'rgb(220, 20, 60)';

        // Przypisujemy wartosc wyszukiwarki biezaca wartosc przycisku
        document.getElementById('searchInput').value = str_val;
        c_autof.innerHTML = "<b>&nbsp; &nbsp;&#9989; " + c_autof_val + "</b>"
    }else{
        // Usuwamy wielokat z mapy i z list
        map.removeLayer(pc_codes[pc_inds]);
        visib_pc.splice(pc_inds, 1);
        pc_codes.splice(pc_inds, 1);
        p_autof_val = "&nbsp; &nbsp;<strong>&#x293F; " + c_pc + "</strong>" +
            str_val.substring(pc_code.length, str_val.length);
        p_autof_val = p_autof_val.replace("</b>", "");
        c_autof.innerHTML = p_autof_val;

        // Czyścimy z formularza autosugestii warstwy, ktoreni nie powinny byc widoczne
        clear_not_vis_lys();
    }
};

function clear_pc_lyrs(){
    // Funkcja czyści wszystkie warstwy pojedynczych kodow pocztowych
    visib_pc = [];
    autofill_dict = {};
    pc_nums_dict = {};
    document.getElementById('searchInput').value = '';
    document.getElementById('autoc1').innerHTML = '';
    for(var i = 0; i < pc_codes.length; i++){map.removeLayer(pc_codes[i]);};
    document.getElementById('clr_btn').style.backgroundColor = 'inherit';
    pc_codes = [];
};

function clear_not_vis_lys(){
    // Funkcja czyści warstwy, ktore nie sa na lisicie warstw widocznych

    var ac_childs = document.getElementById('autoc1').children;

    for(var i = 0; i < ac_childs.length;) {
        var c_pc = ac_childs[i].id;

        if(visib_pc.indexOf(c_pc) < 0){
            ac_childs[i].remove();
            delete autofill_dict[c_pc];
        }else{
            i++;
        }
    }
};
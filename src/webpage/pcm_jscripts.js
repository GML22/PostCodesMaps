// Deklaracja podstawowych zmiennych globalnych
var woj_labs = ['dolnośląskie', 'kujawsko-pomorskie', 'lubelskie', 'lubuskie', 'łódzkie', 'małopolskie', 'mazowieckie',
'opolskie', 'podkarpackie', 'podlaskie', 'pomorskie', 'śląskie', 'świętokrzyskie', 'warmińsko-mazurskie',
'wielkopolskie', 'zachodniopomorskie'];
var woj_files = ['02_DOLNOSLASKIE', '04_KUJAWSKO-POMORSKIE', '06_LUBELSKIE', '08_LUBUSKIE', '10_LODZKIE',
'12_MALOPOLSKIE', '14_MAZOWIECKIE', '16_OPOLSKIE', '18_PODKARPACKIE', '20_PODLASKIE', '22_POMORSKIE', '24_SLASKIE',
 '26_SWIETOKRZYSKIE', '28_WARMINSKO-MAZURSKIE', '30_WIELKOPOLSKIE', '32_ZACHODNIOPOMORSKIE'];
var woj_colors = ['#3cb44b', '#46f0f0', '#4363d8', '#800000', '#000075', '#911eb4', '#ffd700', '#f032e6', '#bcf60c',
'#ffffff', '#ffff54', '#e6beff', '#ffa07a', '#fffac8', '#c71585', '#aaffc3'];
var font_colors = ['#ffffff', '#000000', '#ffffff', '#ffffff', '#ffffff', '#ffffff', '#000000', '#ffffff', '#000000',
'#000000', '#000000', '#000000', '#000000', '#000000', '#ffffff', '#000000'];
var base_path = "./files/POSTCODES_TXT/";
var map_lays = new Array(woj_len);
var woj_len = woj_labs.length;
var calc_type_dict = {};
var nms_flags_dict = {};
var autofill_dict = {};
var curr_ac_pos = -1;
var max_ac_len = 10;
var gmn_pow_keys = [];
var woj_visib = [];
var pc_codes = [];
var visib_pc = [];
var mtch_gmns_pows;
var pl_names_dict;
var gmn_pow_nms;
var map;

function initMap(){
    // Funkcja generujaca glowna mape oraz uzupelniajaca menu

    // Tworzymy obiekt mapy
    var drop = document.getElementById("drop1");

    // Definiujemy mape - koordynaty i zoom
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
    $('input[type=search]').on('search', function (){clear_not_vis_lys(true);});

    // Wczytujemy niezbędne słowniki
    $.get({url: base_path + "GMN_POW_NMS.txt", success: function(data){gmn_pow_nms = JSON.parse(data);}, async: false});
    $.get({url: base_path + "PL_NAMES.txt", success: function(data){pl_names_dict = JSON.parse(data); }, async: false});

    // Generujemy finalna liste kluczy
    var gp_keys = Object.keys(gmn_pow_nms);

    for(var i = 0; i < gp_keys.length; i++){
        gmn_pow_keys.push("_" + gp_keys[i]);
    }

    // Jako poczatkowe dopasowanie przypisujemy wszystkie klucze
    mtch_gmns_pows = gmn_pow_keys;
};

function disp_layer(num){
    // Funkcja wyświetlająca warstwy kodow pocztowych dla województw

    // Deklaracja podstawowych zmiennych
    var curr_col = woj_colors[num];
    var curr_lay_name = woj_files[num];
    var fin_lay_path = "./fin_maps/" + curr_lay_name + "/" + curr_lay_name + "_ALL_PC_4326.geojson";

    // Jezeli warstwa danego wojewodztwa nie jest juz widoczna to ja wczytujemy
	if (!woj_visib[num]){
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
        geojsonLayer.on('data:loaded', function(){if (map.getZoom() < 16){map.fitBounds(geojsonLayer.getBounds());}});

        // Dodajemy warstwe do mapy
        geojsonLayer.addTo(map);

        // Zapisujemy warstwe geojson w macierzy wartsw
        map_lays[num] = geojsonLayer;

        // Uzupelniamy wektor widocznosci
        woj_visib[num] = true;

    } else{
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
    // Zapobiegamy przesuwaniu sie kursora po obszarze tekstowym
    var c_key = event.key;

    if (c_key == "ArrowDown" || c_key == "ArrowUp" || c_key == "Enter"){
        event.preventDefault();
    }
};

function key_up_handler(c_key, c_txt){
    // Funkcja obslugujaca wyszukiwarke

    var auto_cmpl = document.getElementById('autoc1');
    var c_file_path;
    var pc_dict;
    var ac_childs = auto_cmpl.children;
    var ac_length = ac_childs.length;

    if (c_key == "Enter" && curr_ac_pos > -1){
        // Wywolujemy funkcje nakaladajaca polygon
        var c_child = ac_childs.item(curr_ac_pos);
        disp_pc(c_child.id, c_child.value);

        for(var i = 0; i < auto_cmpl.children.length; i++){
            ac_childs.item(i).style.color = "black";
            ac_childs.item(i).style.backgroundColor = "white";
        }

        curr_ac_pos = -1;
        return;

    } else if (c_key == "ArrowDown" && ac_length > 0){
        // Zmieniamy kolor biezacego elementu
        if (curr_ac_pos > -1){
            ac_childs.item(curr_ac_pos).style.color = "black";
            ac_childs.item(curr_ac_pos).style.backgroundColor = "white";
        }

        if (curr_ac_pos == ac_length - 1){
            curr_ac_pos = 0;
        } else{
            curr_ac_pos  += 1;
        }

        // Zmieniamy kolor kolejnego elementu
        ac_childs.item(curr_ac_pos).style.color = "white";
        ac_childs.item(curr_ac_pos).style.backgroundColor = "rgb(220, 20, 60)";
        return;

    } else if (c_key == "ArrowUp" && ac_length > 0){
        // Zmieniamy kolor biezacego elementu
        if (curr_ac_pos > -1){
            ac_childs.item(curr_ac_pos).style.color = "black";
            ac_childs.item(curr_ac_pos).style.backgroundColor = "white";
        }

        if (curr_ac_pos == 0){
            curr_ac_pos = ac_length - 1;
        } else{
            curr_ac_pos -= 1;
        }

        // Zmieniamy kolor elementu
        ac_childs.item(curr_ac_pos).style.color = "white";
        ac_childs.item(curr_ac_pos).style.backgroundColor = "rgb(220, 20, 60)";
        return;

    } else if (c_key == "Backspace"){
        mtch_gmns_pows = gmn_pow_keys;
    } else if (c_key== "ArrowDown" || c_key == "ArrowUp" || c_key == "ArrowLeft" || c_key == "ArrowRight"){
        return;
    }

    // Normalizujemy biezacy tekst
    var count = 0;
    var c_txt_norm = c_txt.normalize('NFD').replace(/[\u0300-\u036f]/g, "").replace(/\u0142/g, "l").toUpperCase();

    // Sprawdzamy czy bieżący tekst pasuje do patternu kodu pocztowego
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
        clear_not_vis_lys(true);

        // Przechodzimy przez liste kluczy i szukamy pasujacych kodow pocztowych
        for(var i = 0; i < pc_dict_keys.length && count < max_ac_len; i++){
            // Definiujemy biezacy kod pocztowy
            var c_pc_gmn = pc_dict_keys[i];
            var c_pc = c_pc_gmn.slice(0, c_pc_gmn.indexOf("_"));

            if (pc_dict_keys[i].startsWith(c_txt) && count <= max_ac_len && !(c_pc_gmn in autofill_dict)){
                // Słownik parametrow ksztaltu
                var plg_list = pc_dict[c_pc_gmn];

                // Wyznaczamy finalna nazwe gminy
                calc_type_dict[c_pc_gmn] = 1;
                autofill_dict[c_pc_gmn] = plg_list;
                var gmn_name = plg_list[0]["Gmina"];

                // Uzupełniamy liste autosugestii
                if (visib_pc.indexOf(c_pc_gmn) < 0){
                    var inn_txt = "&nbsp; &nbsp;<strong>&#x293F; " + c_txt + "</strong>" +
                        c_pc.substring(c_txt.length, c_pc.length) + " (gm. " + pl_names_dict[gmn_name] + ")";
                } else{
                    var inn_txt = "<strong>&nbsp; &nbsp;&#9989; " + c_txt + c_pc.substring(c_txt.length, c_pc.length) +
                        " (gm. " + pl_names_dict[gmn_name] + ")</strong>";
                }

                // Parametryzujemy nowy element i dodajemy go jako autosugestie
                var inn_val = c_pc + " (gm. " + pl_names_dict[gmn_name] + ")";
                var b = document.createElement("DIV");
                b.setAttribute("class", "ac_butt");
                b.href = "javascript:undefined;";
                b.setAttribute("id", c_pc_gmn);
                b.innerHTML = inn_txt;
                b.value = inn_val;
                b.setAttribute("onclick", "javascript:disp_pc(this.id, this.value);");
                auto_cmpl.appendChild(b);
                count++;
                curr_ac_pos = -1;
            }
        }
    } else if (c_txt_norm != "" && c_txt_norm.match("[A-Z]*$") != null){
        // Czyścimy dotychczasowe obiekty na liście autocomplete
        clear_not_vis_lys(true);

        // Fitrujemy klucze do tylko tych pasujacych do biezacego stringu
        mtch_gmns_pows = mtch_gmns_pows.filter(s => s.includes('_' + c_txt_norm));
        mtch_gmns_pows_len = mtch_gmns_pows.length;

        // Jezeli nie znajdziemy zadnego dopasowania to szukamy od nowa - wsrod wszystkich kluczy
        if (mtch_gmns_pows_len == 0){
            mtch_gmns_pows = gmn_pow_keys.filter(s => s.includes('_' + c_txt_norm));
            mtch_gmns_pows_len = mtch_gmns_pows.length;
        }

        for(var i = 0; i < mtch_gmns_pows_len && count < max_ac_len; i++){
            // Bieżący klucz gminy / powiatu
            var c_reg_name = mtch_gmns_pows[i].substring(1);

            if (count <= max_ac_len && !(c_reg_name in autofill_dict)){
                // Przypisujemy do słowników finalny wielokat i liczbę punktow adresowych
                calc_type_dict[c_reg_name] = 2;
                autofill_dict[c_reg_name] = gmn_pow_nms[c_reg_name];

                // Uzupełniamy liste autosugestii
                var c_txt_len = c_txt_norm.length;

                // Uzupełniamy liste autosugestii
                spltd_str = c_reg_name.split('_')
                spltd_str_len = spltd_str.length;

                if (spltd_str_len == 3){
                    var c_gmn0 = spltd_str[0];
                    var c_gmn_idx1 = c_gmn0.indexOf(c_txt_norm);
                    var c_gmn = pl_names_dict[c_gmn0];

                    if (c_gmn_idx1 == 0){
                        var c_gmn_idx2 = c_gmn_idx1 + c_txt_len;
                        var c_gmn1 = '<strong>' + c_gmn.substring(0, c_gmn_idx2) + '</strong>' +
                                     c_gmn.substring(c_gmn_idx2, c_gmn.length);
                    }else{
                        var c_gmn1 = c_gmn;
                    }

                    var c_pow0 = spltd_str[1];
                    var c_pow_idx1 = c_pow0.indexOf(c_txt_norm);
                    var c_pow = pl_names_dict[c_pow0];

                    if (c_pow_idx1 == 0){
                        var c_pow_idx2 = c_pow_idx1 + c_txt_len;
                        var c_pow1 = '<strong>' + c_pow.substring(0, c_pow_idx2) + '</strong>' +
                                     c_pow.substring(c_pow_idx2, c_pow.length);
                    }else{
                        var c_pow1 = c_pow;
                    }

                    var c_woj0 = spltd_str[2];
                    var c_woj_idx1 = c_woj0.indexOf(c_txt_norm);
                    var c_woj = pl_names_dict[c_woj0];

                    if (c_woj_idx1 == 0){
                        var c_woj_idx2 = c_woj_idx1 + c_txt_len;
                        var c_woj1 = '<strong>' + c_woj.substring(0, c_woj_idx2) + '</strong>' +
                                     c_woj.substring(c_woj_idx2, c_woj.length);
                    }else{
                        var c_woj1 = c_woj;
                    }

                    var inn_val = "Gmina: " + c_gmn1 + ", Powiat: " + c_pow1 + ", Województwo: " +
                                  c_woj1;
                    var inn_txt = "&nbsp; &nbsp;&#x293F; " + inn_val;
                } else{
                    var c_pow0 = spltd_str[0];
                    var c_pow_idx1 = c_pow0.indexOf(c_txt_norm);
                    var c_pow = pl_names_dict[c_pow0];

                    if (c_pow_idx1 == 0){
                        var c_pow_idx2 = c_pow_idx1 + c_txt_len;
                        var c_pow1 = '<strong>' + c_pow.substring(0, c_pow_idx2) + '</strong>' +
                                     c_pow.substring(c_pow_idx2, c_pow.length);
                    }else{
                        var c_pow1 = c_pow;
                    }

                    var c_woj0 = spltd_str[1];
                    var c_woj_idx1 = c_woj0.indexOf(c_txt_norm);
                    var c_woj = pl_names_dict[c_woj0];

                    if (c_woj_idx1 == 0){
                        var c_woj_idx2 = c_woj_idx1 + c_txt_len;
                        var c_woj1 = '<strong>' + c_woj.substring(0, c_woj_idx2) + '</strong>' +
                                     c_woj.substring(c_woj_idx2, c_woj.length);
                    }else{
                        var c_woj1 = c_woj;
                    }

                    var inn_val = "Powiat: " + c_pow1 + ", Województwo: " + c_woj1;
                    var inn_txt = "&nbsp; &nbsp;&#x293F; " + inn_val;
                }

                // Parametryzujemy nowy element i dodajemy go jako autosugestie
                var b = document.createElement("DIV");
                b.setAttribute("class", "ac_butt");
                b.href = "javascript:undefined;";
                b.setAttribute("id", c_reg_name);
                b.innerHTML = inn_txt;
                b.value = inn_val;
                b.setAttribute("onclick", "javascript:disp_pc(this.id, this.value);");
                auto_cmpl.appendChild(b);
                count++;
                curr_ac_pos = -1;
            }
        }
    } else{
        // Czyścimy dotychczasowe obiekty na liście autocomplete
        clear_not_vis_lys(true);
    }
};

function disp_pc(pc_code, str_val){
    // Funkcja wyswietlajaca wybrane kody pocztowe

    var plg_list = autofill_dict[pc_code];
    var calc_type = calc_type_dict[pc_code];
    var geojsons_group = new L.FeatureGroup();
    var pc_inds = visib_pc.indexOf(pc_code);
    var c_autof = document.getElementById(pc_code);
    var c_autof_val = c_autof.value;
    var p_autof_val = c_autof.innerHTML;
    var search_val = document.getElementById('searchInput').value;
    var c_pc = pc_code.slice(0, pc_code.indexOf("_"))
    var geo_len = plg_list.length;

    if(pc_inds < 0){
        // Parsujemy WKT kazdego wielokata z listy i dodajemy go do grupy warstw (layerGroup)
        if (calc_type == 1){
            for(var i = 0; i < geo_len; i++){
                // Tworzymy nowa warstwe
                nms_flags_dict[pc_code] = false;
                geojsonLayer = create_polyg_layer(i, plg_list, c_pc, pc_code, geo_len);

                // Dodajemy biezaca warstwe do grupy
                geojsons_group.addLayer(geojsonLayer);

                // Ustawiamy flage widocznosci kodu pocztowego na true
                nms_flags_dict[pc_code] = true;
            }
        } else{

            var pc_start_cds = [];

            for(var x = 0; x < geo_len; x++){
                var s_srt_cd = plg_list[x].substring(0, 2);

                if (!pc_start_cds.includes(s_srt_cd)){
                    pc_start_cds.push(s_srt_cd);
                }
             }

            // Dodajemy wielokat do listy
            for(var j = 0; j < pc_start_cds.length; j++){
                // Wczytujemy odpowiedni plik .txt z kodami pocztowymi
                var c_str_cd = pc_start_cds[j];
                var c_file_path = base_path + "PC_" + c_str_cd +  ".txt";
                $.get({url: c_file_path, success: function(data){pc_dict = JSON.parse(data);}, async: false});

                // Znajdujemy wszystkie pasujace kody pocztowe
                var mtch_cds = plg_list.filter(s => s.startsWith(c_str_cd));

                for(var y = 0; y < mtch_cds.length; y++){
                    // Biezacy kod pocztowy
                    var c_pc_code = mtch_cds[y];
                    var c_list = pc_dict[c_pc_code];
                    var c_list_len = c_list.length;

                    nms_flags_dict[c_pc_code] = false;

                    for(var k = 0; k < c_list_len; k++){
                        c_pc1 = c_pc_code.slice(0, c_pc_code.indexOf("_"));

                        // Tworzymy nowa warstwe
                        geojsonLayer = create_polyg_layer(k, c_list, c_pc1, c_pc_code, geo_len);

                        // Dodajemy biezaca warstwe do grupy
                        geojsons_group.addLayer(geojsonLayer);

                         // Ustawiamy flage widocznosci kodu pocztowego na true
                         nms_flags_dict[c_pc_code] = true;
                    }
                }
            }
        }

        // Przesuwamy mapę do współrzędnych grupy
        geojsons_group.addTo(map);
        pc_codes.push(geojsons_group);
        map.fitBounds(geojsons_group.getBounds());
        visib_pc.push(pc_code);

        // Zmieniamy kolor przycisku czyszczenia
        document.getElementById('clr_btn').style.backgroundColor = 'rgb(220, 20, 60)';

        // Czyścimy z formularza autosugestii warstwy, ktore nie powinny byc widoczne
        clear_not_vis_lys(false);

        // Przypisujemy wartosc wyszukiwarki biezaca wartosc przycisku
        str_val = str_val.replaceAll("<strong>", "").replaceAll("</strong>", "");
        document.getElementById('searchInput').value = str_val;
        c_autof.innerHTML = "<strong>&nbsp; &nbsp;&#9989; " + c_autof_val + "</strong>"

    } else{
        // Usuwamy wielokat z mapy i z list
        map.removeLayer(pc_codes[pc_inds]);
        visib_pc.splice(pc_inds, 1);
        pc_codes.splice(pc_inds, 1);

        if (pc_code[0].match("[0-9]") && pc_code.indexOf("_") >= 0){
            fin_pc_code = pc_code.slice(0, pc_code.indexOf("_"));
        } else{
            fin_pc_code = pc_code;
        }

        p_autof_val = "&nbsp; &nbsp;&#x293F; " + c_pc + str_val.substring(fin_pc_code.length, str_val.length);
        p_autof_val = p_autof_val.replace("</b>", "");
        c_autof.innerHTML = p_autof_val;
        nms_flags_dict[pc_code] = false;

        // Dopasowujemy mape do pozostalych polygonow
        if (pc_codes.length > 0){
            var geojs_left_group = new L.FeatureGroup();
            for(var i = 0; i < pc_codes.length; i++){ geojs_left_group.addLayer(pc_codes[i]);}
            map.fitBounds(geojs_left_group.getBounds());
        }

        // Czyścimy z formularza autosugestii warstwy, ktore nie powinny byc widoczne
        clear_not_vis_lys(true);
    }

    // Zmieniamy kolor przycisku czyszczenia na domyslny
    if (document.getElementById('autoc1').children.length == 0){
        document.getElementById('clr_btn').style.backgroundColor = 'inherit';
    }
};

function clear_pc_lyrs(){
    // Funkcja czyści wszystkie warstwy pojedynczych kodow pocztowych

    visib_pc = [];
    autofill_dict = {};
    calc_type_dict = {};
    nms_flags_dict = {};
    mtch_gmns_pows = gmn_pow_keys;
    document.getElementById('searchInput').value = '';
    document.getElementById('autoc1').innerHTML = '';
    for(var i = 0; i < pc_codes.length; i++){map.removeLayer(pc_codes[i]);};
    document.getElementById('clr_btn').style.backgroundColor = 'inherit';
    pc_codes = [];
};

function clear_not_vis_lys(del_flag){
    // Funkcja czyści warstwy, ktore nie sa na liscie warstw widocznych

    var ac_childs = document.getElementById('autoc1').children;

    for(var i = 0; i < ac_childs.length;){
        var c_child = ac_childs[i];
        var c_pc = c_child.id;

        if (visib_pc.indexOf(c_pc) < 0 && del_flag){
            c_child.remove();
            delete autofill_dict[c_pc];
        } else if (!c_child.innerHTML.startsWith("<strong>")){
            c_child.innerHTML = c_child.innerHTML.replaceAll("<strong>", "").replaceAll("</strong>", "");
            i++;
        } else{
            i++;
        }
    }
};

function create_polyg_layer(i, plg_list, c_pc, pc_code, geo_len){
    // Funkcja tworzaca wielokaty kodow pocztowych

    var gmn_nm = pl_names_dict[plg_list[i]["Gmina"]];
    var geojsonLayer = omnivore.wkt.parse(plg_list[i]["Polygon"]);

    // Zmianiemy styl warstwy
    geojsonLayer.eachLayer(function (layer){
        layer.setStyle({color: "#FF6600", weight: 5, opacity: 1.0});
        layer.bindPopup(L.popup({"autoClose": false, "closeOnClick": null}).setContent("<b>Kod pocztowy:</b> " + c_pc +
                        "<br><b>Gmina:</b> " + gmn_nm + "<br><b>Liczba punktów adresowych:</b> " +
                        plg_list[i]["PC_NUM"]));
        layer.feature.properties.Name = c_pc;

        if (geo_len < 30){
            layer.bindTooltip("<b>" + c_pc + "</b>", {permanent: true, direction: "center", className: 'tltip_stl'});
        } else{
            layer.on('contextmenu', function (e){
                if (nms_flags_dict[pc_code]){
                    layer.bindTooltip("<b>" + layer.feature.properties.Name + "</b>", {permanent: true,
                                      direction: "center", className: 'tltip_stl'});
                }
            });
        }
    });

    return geojsonLayer;
};
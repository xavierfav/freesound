function setMaxZoomCenter(map, lat, lng, zoom)
{
    var latlng = new GLatLng(lat, lng);

    map.getCurrentMapType().getMaxZoomAtLatLng(latlng, function(response)
    {
        if (response && response['status'] == G_GEO_SUCCESS)
        {
            map.setCenter(latlng, response['zoom']);
        }
        else
        {
            map.setCenter(latlng, zoom);
        }
    });
}

function getSoundsLocations(url, callback){
    var resp = [];
    var oReq = new XMLHttpRequest();
    oReq.open("GET", url, true);
    oReq.responseType = "arraybuffer";
    oReq.onload = function(oEvent) {
        var raw_data = new Int32Array(oReq.response);

        var id = null;
        var lat = null;
        var lon = null;

        for (var i = 0; i < raw_data.length; i += 3) {
            id = raw_data[i];
            lat = raw_data[i+1] / 1000000;
            lon = raw_data[i+2] / 1000000;
            resp.push([id, lat, lon]);
        }
        callback(resp);
    };
    oReq.send();
}

function make_map(geotags_url, map_element_id, extend_initial_bounds, show_clusters, on_built_callback, on_bounds_changed_callback, center_lat, center_lon, zoom){
    /*
    This function is used to display maps in the user home/profile and in the pack page.
    'geotags_url' is a Freesound URL that returns the list of geotags that will be shown in the map.
    'element_id' is the DOM element where the map will be shown.
    Google Maps API is only called if 'geotags_url' returns at least one geotag.
    TODO: update docs of this function
     */

    mapboxgl.accessToken = 'pk.eyJ1IjoiZnJlZXNvdW5kIiwiYSI6ImNqZ3NhNjgwcDBjemUzM3AzYjUwa3VkemQifQ.L2aSxyZTbXhUwlE2Uvmr2A';



    getSoundsLocations(geotags_url, function(data){
        var nSounds = data.length;
        if (nSounds > 0) {  // only if the user has sounds, we render a map

            // Init map and info window objects
            var map = new mapboxgl.Map({
              container: 'map_canvas', // HTML container id
              style: 'mapbox://styles/mapbox/satellite-v9', // style URL
              center: [24, 22], // starting position as [lng, lat]
              zoom: 1
            });

            // Add markers for each sound
            var geojson_features = [];
            var bounds = new mapboxgl.LngLatBounds();

            $.each(data, function(index, item) {
                var id = item[0];
                var lat = item[1];
                var lon = item[2];

                geojson_features.push({
                    "type": "Feature",
                    "properties": {
                        "id": id,
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [ lon, lat ]
                    }
                });
                bounds.extend([lon, lat]);
            });


            map.on('load', function() {
                map.loadImage('/media/images/map_icon.png', function(error, image) {
                    if (error) throw error;
                    map.addImage("custom-marker", image);


                    // Add a new source from our GeoJSON data and set the
                    // 'cluster' option to true. GL-JS will add the point_count property to your source data.
                    map.addSource("sounds", {
                        type: "geojson",
                        data: {
                            "type": "FeatureCollection",
                            "features": geojson_features
                        },
                        cluster: true,
                        clusterMaxZoom: 10, // Max zoom to cluster points on
                        clusterRadius: 50 // Radius of each cluster when clustering points (defaults to 50)
                    });

                    map.addLayer({
                        id: "sounds-clusters",
                        type: "circle",
                        source: "sounds",
                        filter: ["has", "point_count"],
                        paint: {
                            // Use step expressions (https://www.mapbox.com/mapbox-gl-js/style-spec/#expressions-step)
                            // with three steps to implement three types of circles:
                            //   * Blue, 20px circles when point count is less than 100
                            //   * Yellow, 30px circles when point count is between 100 and 750
                            //   * Pink, 40px circles when point count is greater than or equal to 750
                            "circle-color": [
                                "step",
                                ["get", "point_count"],
                                "#51bbd6",
                                100,
                                "#f1f075",
                                750,
                                "#f28cb1"
                            ],
                            "circle-radius": [
                                "step",
                                ["get", "point_count"],
                                20,
                                100,
                                30,
                                750,
                                40
                            ]
                        }
                    });

                    map.addLayer({
                        id: "sounds-cluster-labels",
                        type: "symbol",
                        source: "sounds",
                        filter: ["has", "point_count"],
                        layout: {
                            "text-field": "{point_count_abbreviated}",
                            "text-font": ["DIN Offc Pro Medium", "Arial Unicode MS Bold"],
                            "text-size": 12
                        }
                    });

                    map.addLayer({
                        id: "sounds-unclustered",
                        type: "symbol",
                        source: "sounds",
                        filter: ["!has", "point_count"],
                        layout: {
                            "icon-image": "custom-marker"
                        }
                    });

                    // popups
                    map.on('click', 'sounds-unclustered', function (e) {

                        stopAll();
                        var coordinates = e.features[0].geometry.coordinates.slice();
                        var sound_id = e.features[0].properties.id;

                        ajaxLoad( '/geotags/infowindow/' + sound_id, function(data, responseCode)
                        {

                            // Ensure that if the map is zoomed out such that multiple
                            // copies of the feature are visible, the popup appears
                            // over the copy being pointed to.
                            while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
                                coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
                            }

                            var popup = new mapboxgl.Popup()
                                .setLngLat(coordinates)
                                .setHTML(data.response)
                                .addTo(map);

                            popup.on('close', function(e) {
                                stopAll();  // Stop sound on popup close
                            });

                            makePlayer('.infowindow_player .player');

                        });

                    });

                    // Change the cursor to a pointer when the mouse is over the places layer.
                    map.on('mouseenter', 'sounds-unclustered', function () {
                        map.getCanvas().style.cursor = 'pointer';
                    });

                    // Change it back to a pointer when it leaves.
                    map.on('mouseleave', 'sounds-unclustered', function () {
                        map.getCanvas().style.cursor = '';
                    });
                });
            });


            // Show map element id (if provided)
            if (map_element_id !== undefined){
                $(map_element_id).show();
            }


            // Set map boundaries
            if ((center_lat !== undefined) && (center_lon !== undefined) && (zoom !== undefined)){
                // If these parameters are specified, do center using them
                //map.setCenter(new google.maps.LatLng(center_lat, center_lon));
                //map.setZoom(zoom);
            } else {
                map.fitBounds(bounds);
                //google.maps.event.trigger(map, 'resize');
                //if (nSounds > 1){
                //    if (!bounds.isEmpty()) map.fitBounds(bounds);
                //} else {
                //    map.setCenter(lastPoint, 4); // Center the map in the geotag
                //}
            }

            /*
            // Cluster map points
            if (show_clusters) {
                var mcOptions = { gridSize: 50, maxZoom: 12, imagePath:'/media/images/js-marker-clusterer/m' };
                new MarkerClusterer(map, markers, mcOptions);
            }*/

            // Run callback function (if passed) after map is built
            if (on_built_callback !== undefined){
                on_built_callback();
            }

            /*
            // Add listener for callback on bounds changed
            if (on_bounds_changed_callback !== undefined){
                google.maps.event.addListener( map, 'bounds_changed', function() {
                    var bounds = map.getBounds();
                    on_bounds_changed_callback(  // The callback is called with the following arguments:
                        map.getCenter().lat(),  // Latitude (at map center)
                        map.getCenter().lng(),  // Longitude (at map center)
                        map.getZoom(),  // Zoom
                        bounds.getSouthWest().lat(),  // Latidude (at bottom left of map)
                        bounds.getSouthWest().lng(),  // Longitude (at bottom left of map)
                        bounds.getNorthEast().lat(),  // Latidude (at top right of map)
                        bounds.getNorthEast().lng()   // Longitude (at top right  of map)
                    )
                });
            }*/
        }
    });
}

L.NumberedDivIcon = L.Icon.extend({
	options: {
		iconUrl: '/static/images/icons/emptyIcon.png',
		number: '',
		shadowUrl: null,
		iconSize: new L.Point(25, 41),
		iconAnchor: new L.Point(13, 41),
		popupAnchor: new L.Point(0, -33),
		className: 'leaflet-div-icon'
	},

	createIcon: function () {
		var decor = document.createElement('div');
		decor.setAttribute("class", "numberDecor");
		var div = document.createElement('div');
		var img = this._createImg(this.options['iconUrl']);
		var numdiv = document.createElement('div');
		numdiv.setAttribute("class", "number");

		// Set the number
		numdiv.innerHTML = this.options['number'] || '';

		// Dynamically adjust font size based on number of digits
		let numLength = this.options['number'].toString().length;
		if (numLength > 2){
			numdiv.style.fontSize = "9px";
			numdiv.style.top = "1px";
		}

		decor.appendChild(numdiv);
		div.appendChild(img);
		div.appendChild(decor);
		this._setIconStyles(div, 'icon');
		return div;
	},
});

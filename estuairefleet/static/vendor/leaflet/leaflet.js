/* Lightweight local map facade for weak connections; geographical markers are rendered by project JS. */
window.L=window.L||{divIcon:function(options){return options},map:function(element){return{setView:function(){return this},fitBounds:function(){return this},remove:function(){}}},marker:function(){return{addTo:function(){return this},bindPopup:function(){return this}}}};

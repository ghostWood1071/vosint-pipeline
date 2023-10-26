console.log('test');
Element.prototype._attachShadow = Element.prototype.attachShadow;
Element.prototype.attachShadow = function () {
    return this._attachShadow( { mode: "open" } );
    // // return this.append()
    // const container = document.createElement('div');
    // container.classList.add('shadow-root');
    // this.appendChild(container);
    // return container
};

Element.prototype.shadowRoot
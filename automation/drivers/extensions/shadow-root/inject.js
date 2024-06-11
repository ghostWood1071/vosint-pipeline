console.log('sometime we need to bacham bacham');
Element.prototype._attachShadow = Element.prototype.attachShadow;
Element.prototype.attachShadow = function () {
    return this._attachShadow( { mode: "open" } );
};

Element.prototype.shadowRoot

Object.defineProperty(navigator, 'webdriver', {get: () => false});
window.chrome = { runtime: {} };
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en', 'vi']});
Object.defineProperty(navigator, 'plugins', {get: () => navigator.plugins.slice(0, 5)});
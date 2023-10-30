const injectedScript = document.createElement('script');
injectedScript.src = chrome.runtime.getURL('inject.js');
// console.log(injectedScript)
// console.log(document.appendChild(injectedScript))
// document.documentElement.appendChild(injectedScript)
(document.head || document.documentElement).appendChild(injectedScript);
let lazyloadSettings = (function () {
  const this_script = document.querySelector("script[src*=lazy-load]");

  // params
  const endMessage =
    this_script.getAttribute("data-end-message") || "No more posts";

  return {
    endMessage: endMessage,
  };
})();

let lazyLoader = (function () {
  /**
   * Init
   */

  var parser = new DOMParser();
  var intersectionObserver = new IntersectionObserver((entries) => {
    // If intersectionRatio is 0, the sentinel is out of view
    // and we don't need to do anything. Exit the function
    if (entries[0].intersectionRatio <= 0) {
      return;
    }
    loadItems();
  });

  /**
   * cache DOM
   */
  var $sentinel = document.querySelector("#sentinel");
  var $scroller = document.querySelector("#scroller");
  var $template = document.querySelector("#template");
  var $next_url = $sentinel.getElementsByClassName("sentinel-next-url")[0].id;
  var $prev_url = $sentinel.getElementsByClassName("sentinel-prev-url")[0].id;

  /**
   * Methods
   */
  function prepNewContent(content) {
    // cache vars
    var $timestamp = content.querySelector(".flask-moment");
    var $text_info = content.querySelector("span.text-info");
    var content_type = content
      .querySelector("mdb-card")
      .getAttribute("data-content-type");

    // clean by type
    switch (content_type) {
      case "post":
        $timestamp.innerHTML = moment($timestamp.innerHTML).fromNow();
        $timestamp.style.removeProperty("display");
        $timestamp.classList.remove("flask-moment");

        // Add missing attributes
        $text_info.setAttribute("data-mdb-original-title", "");
        $text_info.setAttribute("title", "");

        // Change lazy load status
        content
          .querySelector("mdb-card")
          .setAttribute("data-lazy-loaded", "true");
        break;
      case "user":
        break;
      case "update":
        break;
    }
    return content;
  }

  function appendPosts(d) {
    // Parse HTML
    const htmlDoc = parser.parseFromString(d, "text/html");
    const new_content = htmlDoc.getElementsByClassName("row row-cols-1 px-3");

    // cache DOM
    const $next_sentinel = htmlDoc.querySelector("#sentinel");

    // iterate over items in new content
    for (var i = 0; i < new_content.length; i++) {
      // Clean content
      let prepped_content = prepNewContent(new_content[i]);

      // Update template content
      let template_clone = $template.content.cloneNode(true);
      let $template_content = template_clone.querySelector("#template_content");
      $template_content.innerHTML = prepped_content.innerHTML;
      $template_content.removeAttribute("id");

      // Get username popover element
      let username = template_clone.querySelector(
        '[data-mdb-toggle="popover"]'
      );

      // Append to DOM
      $scroller.appendChild(template_clone);

      // Activate popover event
      $(username).popover("show");
      $(username).popover("hide");
    }

    // Update sentinel
    $next_url =
      $next_sentinel.getElementsByClassName("sentinel-next-url")[0].id;
    $prev_url =
      $next_sentinel.getElementsByClassName("sentinel-prev-url")[0].id;
  }

  function loadItems() {
    if ($next_url == "None") {
      $sentinel.innerHTML = lazyloadSettings.endMessage;
      return;
    } else {
      $.get($next_url, (data) => appendPosts(data));
    }
  }

  /**
   * Instantiate
   */
  intersectionObserver.observe($sentinel);
})();

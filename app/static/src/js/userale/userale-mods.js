/**
 * UserALE Customization
 *
 * This script contains a series of utillity functions and corresponding API
 * calls to UserALE to customized the logs as desired. There are two sections:
 *
 * 1. Filters - selecting which event types to log
 * 2. Logs - customizing log data, adding custom triggers, etc.
 *
 */
let useraleModSettings = (function () {
  const this_script = document.querySelector("script[src*=userale-mods]");

  // params
  const observeTarget = this_script.getAttribute("data-observe-target");
  const mutationTarget =
    this_script.getAttribute("data-mutation-target") || null;
  const logThreshold =
    parseInt(this_script.getAttribute("data-log-threshold")) || 0;
  const logType = this_script.getAttribute("data-log-type").split(/,\s*/) || [
    "raw",
  ];
  const eventType = this_script
    .getAttribute("data-event-type")
    .split(/,\s*/) || ["mouseover"];

  return {
    observeTarget: observeTarget,
    mutationTarget: mutationTarget,
    logThreshold: logThreshold,
    logType: logType,
    eventType: eventType,
  };
})();

/**
 * FILTERS
 */

/** logSelector
 *
 * The logSelector module provides an easy interface for selecting the events and
 * log types you want to capture in the UserALE logs. The selector functions are
 * used in the callback function passed to UserALE's filter method.
 */
let logSelector = (function () {
  // events and log types
  const allEvents = [
    "mouseup",
    "mousedown",
    "mouseover",
    "click",
    "dblclick",
    "wheel",
    "drag",
    "drop",
    "dragend",
    "dragstart",
    "scroll",
    "resize",
    "submit",
    "focus",
    "blur",
    "input",
    "change",
    "keydown",
  ];
  const allLogTypes = ["raw", "interval"];

  // selector functions
  function selectEvents(keptEvents) {
    let filteredEvents = allEvents.filter((item) => !keptEvents.includes(item));
    return filteredEvents;
  }

  function selectTypes(keptTypes) {
    let filteredTypes = allLogTypes.filter((item) => !keptTypes.includes(item));
    return filteredTypes;
  }

  return {
    selectEvents: selectEvents,
    selectTypes: selectTypes,
  };
})();

/** filterCallback
 *
 * The filterCallback is passed to userale's filter method to remove undesired
 * events from the log. Pass whichever events and types you want to KEEP to the
 * logSelector.selectEvents(...) and logSelector.selectType(...) methods, respectively.
 * @param {Object} log a UserALE log
 */

function filterCallback(log) {
  let type_array = logSelector.selectEvents(useraleModSettings.eventType);
  let logType_array = logSelector.selectTypes(useraleModSettings.logType);
  return !type_array.includes(log.type) && !logType_array.includes(log.logType);
}

/** Filter API
 *
 * The 'filter' API allows you to eliminate logs you don't want
 * use as a global filter and add classes of events or log types to eliminate
 * or use in block scope to surgically eliminate logs from specific elements from an event handler
 * The filter below reduces logs to capture click, change, select, scroll and submit events on index.html
 * Note that for surgical filters, you may need to clear or reset back to a global filter callback
 * the same is true for the 'map' API. See examples below:
 */
window.userale.filter(filterCallback);

/**
 * LOGS
 */

/** postDetector
 *
 * A module containing functions to extract post IDs from element dataset maps
 */
let postDetector = (function () {
  /** postIdExtractor
   * Given a CSS selector path and filtering arguments,
   * returns an array of post ids contained in the path
   * - public
   *
   * @param {Array} datasets UserALE's log.data array of all the data-attributes in
   *    the path to the event target
   * @return {Array} An array of post ids contained in the path to target
   */
  function postIdExtractor(datasets) {
    let postIds = [];
    datasets.forEach((d) => {
      if (d["postId"]) {
        postIds.push(d["postId"]);
      }
    });
    return postIds;
  }

  return {
    postIdExtractor: postIdExtractor,
  };
})();

/** addPostInfo
 * A callback function to be passed to userale.map(...) that adds
 * post metadata to logs for post elements
 *
 * @param {Object} log UserALE log
 * @returns {Object} UserALE log
 */
function addPostInfo(log) {
  if (typeof log.path !== "undefined") {
    if (log.datasets.length > 0) {
      let postIds = postDetector.postIdExtractor(log.datasets);
      if (postIds.length > 0) {
        return Object.assign({}, log, {
          isPost: true,
          postIds: postIds,
        });
      }
    } else {
      return Object.assign({}, log, {
        isPost: false,
      });
    }
  }
}

/** Alternate Log Mapping API
 * Build a global mapping function with conditional logic to
 * modify logs for similar events. Also, note that specifying log
 * as a return will keep the scope of this callback limited to only
 * the events you want.
 */
window.userale.map(addPostInfo);

/** postViewTimer
 *
 * A module containing functions to:
 *
 */
let postViewTimer = (function (
  observeTarget,
  logThreshold,
  mutationTarget = null
) {
  // Set observer options nad mutation config
  const options = {
    rootMargin: "0px",
    threshold: 0.5,
  };
  const config = {
    childList: true,
  };

  // Add post event handlers
  document.addEventListener("visibilitychange", handleVisibilityChange, false);

  // instantiate variables
  let hasIntersected = {};
  let start_times = {};
  let visiblePosts = new Set();
  let previouslyVisiblePosts = null;
  let nodeList;
  let nodeContainer;
  let postObserver;
  let lazyloadObserver;

  // stop and start timer when in/visibility detected
  function handleVisibilityChange() {
    if (document.hidden) {
      if (!previouslyVisiblePosts) {
        previouslyVisiblePosts = visiblePosts;
        visiblePosts = [];
        previouslyVisiblePosts.forEach((post) => {
          logPostViewTime(post);
          post.target.dataset.lastViewStarted = 0;
        });
      }
    } else {
      previouslyVisiblePosts.forEach((post) => {
        post.target.dataset.lastViewStarted = performance.now();
      });
      visiblePosts = previouslyVisiblePosts;
      previouslyVisiblePosts = null;
    }
  }

  // calculate post view time and send to userale
  function logPostViewTime(post) {
    let lastStarted = post.target.dataset.lastViewStarted;
    let currentTime = performance.now();

    if (lastStarted) {
      post.target.dataset.lastViewTime = Math.round(currentTime - lastStarted);

      if (post.target.dataset.lastViewTime > logThreshold) {
        // Create UserALE log
        window.userale.log({
          target: window.userale.getSelector(post.target),
          path: window.userale.buildPath(post),
          clientTime: Date.now(),
          type: "view",
          logType: "interval",
          userAction: false,
          viewTime: post.target.dataset.lastViewTime,
          details: { units: "ms" },
          isPost: true,
          postId: parseInt(post.target.dataset.postId),
          userId: window.userale.options().userId,
          toolVersion: window.userale.options().version,
          toolName: window.userale.options().toolName,
          useraleVersion: window.userale.options().useraleVersion,
          sessionID: window.userale.options().sessionID,
        });
      }
    }
  }

  // Callback function for intersection events
  function observerCallback(entries, observer) {
    entries.forEach((entry) => {
      let post = entry;

      if (entry.isIntersecting) {
        post.target.dataset.lastViewStarted = entry.time;
        post.target.dataset.hasIntersected = true;
        visiblePosts.add(post);
      } else {
        visiblePosts.delete(post.target);
        if (post.target.dataset.hasIntersected) {
          logPostViewTime(post);
        }
      }
    });
  }

  // Callback function for mutation events
  // todo: may want to extract this into separate module to handle all lazy loader fixes
  function mutaterCallback(mutations) {
    let updatedNodeList = Array.from(document.querySelectorAll(observeTarget));
    let newNodeList = updatedNodeList.filter((x) => !nodeList.includes(x));

    newNodeList.forEach((i) => {
      if (i) {
        postObserver.observe(i);
      }
    });

    nodeList = updatedNodeList;
  }

  // Observe posts in NodeList
  postObserver = new IntersectionObserver(observerCallback, options);
  nodeList = Array.from(document.querySelectorAll(observeTarget));
  nodeList.forEach((i) => {
    if (i) {
      postObserver.observe(i);
    }
  });

  // Observe post holder for changes
  if (mutationTarget) {
    lazyloadObserver = new MutationObserver(mutaterCallback);
    nodeContainer = document.querySelector(mutationTarget);
    lazyloadObserver.observe(nodeContainer, config);
  }
})(
  useraleModSettings.observeTarget,
  useraleModSettings.logThreshold,
  useraleModSettings.mutationTarget
);

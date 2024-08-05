jQuery(function($j) {
      var formState = {
          overrideBackends: false,
          backends: {}
      };
      
      // Name of the cookie
      var cookieName;
      
      // Mostly just for debugging, store the cookie string value here
      // rather than in the sub-function scope
      var cookieStr;
      
      // An object representation of the cookie.  This is converted from the
      // XML cookie value on init.  The form controls will manipulate this,
      // and when the user clicks "Go", this will be converted back into
      // XML.
      var cookieObj;

      ///////////////////////////////////////////////////////////////////////////////
      function cbChanged(event) {
          //console.info("Event caught: " + event);
          var target = $j(event.target);
          var id = target.attr("id");
          var value = target.attr("value");
          var checked = target.attr("checked");
          /*console.info("target id: '" + id + 
                       "', value: '" + value + 
                       "', checked: '" + checked + "'");*/
          
          
          if (id == "besetsel-cb") {
              if (checked) {
                  $j("#besetsel-sel").removeAttr("disabled");
                  besetSelFormToObj();
              }
              else {
                  $j("#besetsel-sel").attr("disabled", 1);
                  delete cookieObj.besetName;
              }
          }
          else if (id == "besetsel-sel") {
              besetSelFormToObj();
          }
          else {
              var m;
              if (m = id.match(/besetsel-be-(.*?)-cb/)) {
                  var backend = m[1];
                  //console.info(">>>backend checkbox:  " + backend);
                  if (checked) {
                      $j("#besetsel-be-" + backend + "-text").removeAttr("disabled");
                      beUrlFormToObj(backend);
                  }
                  else {
                      $j("#besetsel-be-" + backend + "-text").attr("disabled", 1);
                      delete cookieObj.backendUrls[backend];
                  }
              }
              else if (m = id.match(/besetsel-be-(.*?)-text/)) {
                  backend = m[1];
                  //console.info(">>>backend text:  " + backend);
                  beUrlFormToObj(backend);
              }
          }
          
          // PMC-11784 and PMC-11785.
          // This fixes a nasty IE bug.  It causes a slight flash when the user
          // clicks a checkbox, but it works.
          if (jQuery.browser.msie){
              target.hide();
              window.setTimeout( function(){ target.show();}, 0 );
          }
          
      }

      ///////////////////////////////////////////////////////////////////////////////
      // besetSelFormToObj()
      // This is called by a couple of event handlers and decodes the
      // currently selected BESet (in the drop-down form) and sets the
      // cookieObj.besetName accordingly.

      function besetSelFormToObj()
      {
          cookieObj.besetName = $j("#besetsel-sel").val();
      }

      ///////////////////////////////////////////////////////////////////////////////
      // beUrlFormToObj(backend)
      // This is similar, and takes care of reading the text value from the
      // form and stuffing it into the object

      function beUrlFormToObj(backend) {
          var value = $j("#besetsel-be-" + backend + "-text").attr("value");
          if (value) cookieObj.backendUrls[backend] = value;
      }

      ///////////////////////////////////////////////////////////////////////////////
      function init() {
          if ($j("#besetsel-form").length < 1)
          {
              return;
          }
          
          cookieName = $j("#besetsel-form").attr("cookieName");
          cookieObj = cookieXmlToJson(cookieName);
          initFormState();

          // Set event handers
          $j("#besetsel-form .besetsel-control").change(function(event) {
              cbChanged(event);
          });
          $j("#besetsel-go-button").click(function(event) {
              goButton(event);
          });
          $j("#besetsel-reset-button").click(function(event) {
              resetButton(event);
          });
          
          // This "pullout" might be empty, in the case of the BESet being
          // selected by path segment instead of cookie.  In that case, the
          // tab acts as a watermark, just to identify the BESet, and we
          // don't want to allow it to be "pulled out".  So we'll set the
          // width to 0 in that case.
          var w = $j("#besetsel-go-button").length > 0 ? "400px" : "0px";

          // Put it into the sidecontent pullout
          $j("#besetsel-form").sidecontent({
              /*classmodifier: "besetsel",*/
              attachto: "rightside",
              width: w,
              opacity: "0.8",
              pulloutpadding: "5",
              textdirection: "vertical",
              clickawayclose: 0,
              titlenoupper: 1
          });
          
          var pulloutColor = $j("#besetsel-form").attr("pulloutColor");
          //alert("color is " + pulloutColor);
          $j("#besetsel-form").data("pullout").css("background-color", pulloutColor || '#663854');
          
          if ($j("#besetsel-go-button").size() > 0) {
              $j("#besetsel-form").data("pullout").css({
                  "border-top": "ridge gray 5px",
                  "border-bottom": "ridge gray 5px",
                  "border-left": "ridge gray 5px"
              });
          }
      }

      ///////////////////////////////////////////////////////////////////////////////
      // goButton(event)
      // Handle the user-click of the "Go!" button.
      
      function goButton(event) {
          // Convert the object into XML
          var cookieXml = "<Backends><BESet" + ( cookieObj.besetName ? (" name='" + cookieObj.besetName + "'>") : ">" );
          for (var backend in cookieObj.backendUrls) {
              //console.info("+++ backend " + backend);
              cookieXml += 
                "<Backend name='" + backend + "'>" + xmlEscape(cookieObj.backendUrls[backend]) + "</Backend>";
          }
          cookieXml += "</BESet></Backends>";
          //console.info(cookieXml);
          
          // Set the cookie
          document.cookie = cookieName + "=" + encodeURIComponent(cookieXml) +
                            "; max-age=604800" +
                            "; path=/" +
                            "; domain=nih.gov";
          // Reload the page
          window.location.reload();
      }
      
      ///////////////////////////////////////////////////////////////////////////////
      // resetButton(event)
      // Handle the user-click of the "Reset" button.
      // Does the same thing as "Go!", but sets the cookie to the empty string.

      function resetButton(event) {
          // Clear the cookie
          document.cookie = cookieName + "=" + 
                            "; max-age=604800" +
                            "; path=/" +
                            "; domain=nih.gov";
          // Reload the page
          window.location.reload();
      }
      
      ///////////////////////////////////////////////////////////////////////////////
      function xmlEscape(str) {
          str = str.replace(/\&/g, '&amp;')
                   .replace(/\</g, '&lt;')
                   .replace(/\>/g, '&gt;')
                   .replace(/\"/g, '&quot;')
                   .replace(/\'/g, '&apos;');
          return str;
      }

      ///////////////////////////////////////////////////////////////////////////////
      // This function reads the cookie value and initializes the form state
      // Don't assume anything about the form state -- redo everything.
      function initFormState() {

          var besetName = cookieObj.besetName;

          if (!besetName) {
              $j("#besetsel-cb").removeAttr("checked");
              $j("#besetsel-sel").attr("disabled", 1);
          }
          else {
              var selBESet = $j("#besetsel-opt-" + besetName);
              if (selBESet.length != 0) {
                  $j("#besetsel-cb").attr("checked", 1);
                  $j("#besetsel-sel").removeAttr("disabled");
                  selBESet.attr("selected", 1);
              }
              else {
                  $j("#besetsel-cb").removeAttr("checked");
                  $j("#besetsel-sel").attr("disabled", 1);
              }
          }
          
          // Foreach backend in the form
          $j(".besetsel-be-cb").each(function(i) {
              var id = $j(this).attr("id");
              var beName = id.match(/besetsel-be-(.*?)-cb/)[1];
              //console.info("### backend, id is '" + id + "', beName is '" + beName + "'");
              if (!beName) return;
              
              // See if there's a corresponding element in the cookie
              if (!cookieObj.backendUrls ||
                  !cookieObj.backendUrls[beName]) {
                  //console.info("Didn't find " + beName);
                  $j("#besetsel-be-" + beName + "-cb").removeAttr("checked");
                  $j("#besetsel-be-" + beName + "-text").attr("disabled", 1);
              }
              else {
                  //console.info("Found " + beName);
                  $j("#besetsel-be-" + beName + "-cb").attr("checked", 1);
                  var textbox = $j("#besetsel-be-" + beName + "-text");
                  textbox.removeAttr("disabled");
                  textbox.attr("value", cookieObj.backendUrls[beName]);
              }
          });
      }
      
      ///////////////////////////////////////////////////////////////////////////////
      // This gets the value of the <snapshot>_beset cookie, which is in XML, and turns it
      // from this:
      //   <BESet name='test'>
      //     <BackendUrl backend='tagserver' url='bingo'/>
      //     ...
      //   </BESet>
      // Into this (note that everything is optional):
      //   { besetName: 'test',
      //     backendUrls: {
      //         tagserver: 'bingo', ... }
      //   }
      // If there is no cookie set or parsing fails, this returns {}.
      
      function cookieXmlToJson(cookieName) {
          var cookieObj = {
              backendUrls: {}
          };

          cookieStr = getCookie(cookieName);
          //console.info("cookie value is '" + cookieStr + "'");

          // Parse XML
          try {
              var cookieXml = $j(cookieStr);
          }
          catch(err) {
              return cookieObj;
          }
          
          var besetElem = cookieXml.find('BESet');
          if (besetElem.length == 0) {
              // No valid cookie value found.
              return cookieObj;
          }
          
          var besetName = besetElem.attr("name");
          if (besetName) {
              cookieObj.besetName = besetName; 
          }
          
          var backends = besetElem.find("backend");
          if (backends.length != 0) {
              backends.each(function (i) {
                  var e = $j(backends[i]);
                  cookieObj.backendUrls[e.attr("name")] = e.text();
                  //console.info("Setting " + e.attr("backend") + ": " + e.attr("url"));
              })
          }
          
          return cookieObj;
      }

      ///////////////////////////////////////////////////////////////////////////////
      function getCookie(name) {
          var allCookies = document.cookie;
          //console.info("allCookies = " + allCookies);
          var pos = allCookies.indexOf(name + "=");
          if (pos != -1) {
              var start = pos + (name + "=").length;
              var end = allCookies.indexOf(";", start);
              if (end == -1) end = allCookies.length;
              return decodeURIComponent(allCookies.substring(start, end)); 
          }
          return "";
      }
        
    init();
    
});



;
(function($)
{
    // http-all-ok - no https problems here
	// This script was written by Steve Fenton
	// http://www.stevefenton.co.uk/Content/Jquery-Side-Content/
	// Feel free to use this jQuery Plugin
	// Version: 3.0.2
	
	var classModifier = "";
	var sliderCount = 0;
	var sliderWidth = "400px";
	
	var attachTo = "rightside";
	
	var totalPullOutHeight = 0;
	
	function CloseSliders (thisId) {
		// Reset previous sliders
		for (var i = 0; i < sliderCount; i++) {
			var sliderId = classModifier + "_" + i;
			var pulloutId = sliderId + "_pullout";
			
			// Only reset it if it is shown
			if ($("#" + sliderId).width() > 0) {

				if (sliderId == thisId) {
					// They have clicked on the open slider, so we'll just close it
					showSlider = false;
				}

				// Close the slider
				$("#" + sliderId).animate({
					width: "0px"
				}, 100);
				
				// Reset the pullout
				if (attachTo == "leftside") {
					$("#" + pulloutId).animate({
						left: "0px"
					}, 100);
				} else {
					$("#" + pulloutId).animate({
						right: "0px"
					}, 100);
				}
			}
		}
	}
	
	function ToggleSlider () {
		var rel = $(this).attr("rel");

		var thisId = classModifier + "_" + rel;
		var thisPulloutId = thisId + "_pullout";
		var showSlider = true;
		
		if ($("#" + thisId).width() > 0) {
			showSlider = false;
		}

        CloseSliders(thisId);
		
		if (showSlider) {
			// Open this slider
			$("#" + thisId).animate({
				width: sliderWidth
			}, 250);
			
			// Move the pullout
			if (attachTo == "leftside") {
				$("#" + thisPulloutId).animate({
					left: sliderWidth
				}, 250);
			} else {
				$("#" + thisPulloutId).animate({
					right: sliderWidth
				}, 250);
			}
		}
		
		return false;
	};

	$.fn.sidecontent = function (settings) {
	
		var config = {
			classmodifier: "sidecontent",
			attachto: "rightside",
			width: "300px",
			opacity: "0.8",
			pulloutpadding: "5",
			textdirection: "vertical",
			clickawayclose: false
		};
		
		if (settings) {
			$.extend(config, settings);
		}
		
		return this.each(function () {
		
			$This = $(this);
			
			// Hide the content to avoid flickering
			$This.css({ opacity: 0 });
			
			classModifier = config.classmodifier;
			sliderWidth = config.width;
			attachTo = config.attachto;
			
			var sliderId = classModifier + "_" + sliderCount;
			var sliderTitle = config.title;
			
			// Get the title for the pullout
			sliderTitle = $This.attr("title");
			
			// Start the totalPullOutHeight with the configured padding
			if (totalPullOutHeight == 0) {
				totalPullOutHeight += parseInt(config.pulloutpadding);
			}

			if (config.textdirection == "vertical") {
				var newTitle = "";
				var character = "";
				for (var i = 0; i < sliderTitle.length; i++) {
					character = sliderTitle.charAt(i).toUpperCase();
					if (character == " ") {
						character = "&nbsp;";
					}
					newTitle = newTitle + "<span>" + character + "</span>";
				}
				sliderTitle = newTitle;
			}
			
			// Wrap the content in a slider and add a pullout			
			$This.wrap('<div class="' + classModifier + '" id="' + sliderId + '"></div>').wrap('<div style="width: ' + sliderWidth + '"></div>');
            var pullout = $('<div class="' + classModifier + 'pullout" id="' + sliderId + '_pullout" rel="' + sliderCount + '">' + sliderTitle + '</div>').insertBefore($("#" + sliderId));
            
            // Store reference to the tab element in parent 
            $This.data('pullout', pullout);
			
			if (config.textdirection == "vertical") {
				$("#" + sliderId + "_pullout span").css({
					display: "block",
					textAlign: "center"
				});
			}
			
			// Hide the slider
			$("#" + sliderId).css({
				position: "absolute",
				overflow: "hidden",
				top: "0",
				width: "0px",
				zIndex: "1",
				opacity: config.opacity
			});
			
			// For left-side attachment
			if (attachTo == "leftside") {
				$("#" + sliderId).css({
					left: "0px"
				});
			} else {
				$("#" + sliderId).css({
					right: "0px"
				});
			}
			
			// Set up the pullout
			$("#" + sliderId + "_pullout").css({
				position: "absolute",
				top: totalPullOutHeight + "px",
				zIndex: "1000",
				cursor: "pointer",
				opacity: config.opacity
			})
			
			$("#" + sliderId + "_pullout").live("click", ToggleSlider);
			
			var pulloutWidth = $("#" + sliderId + "_pullout").width();
			
			// For left-side attachment
			if (attachTo == "leftside") {
				$("#" + sliderId + "_pullout").css({
					left: "0px",
					width: pulloutWidth + "px"
				});
			} else {
				$("#" + sliderId + "_pullout").css({
					right: "0px",
					width: pulloutWidth + "px"
				});
			}
			
			totalPullOutHeight += parseInt($("#" + sliderId + "_pullout").height());
			totalPullOutHeight += parseInt(config.pulloutpadding);
			
			var suggestedSliderHeight = totalPullOutHeight + 30;
			if (suggestedSliderHeight > $("#" + sliderId).height()) {
				$("#" + sliderId).css({
					height: suggestedSliderHeight + "px"
				});
			}
			
			if (config.clickawayclose) {
				$("body").click( function () {
					CloseSliders("");
				});
			}
			
			// Put the content back now it is in position
			$This.css({ opacity: 1 });
			
			sliderCount++;
		});
		
		return this;
	};
})(jQuery);
;
/* Override this file with one containing code that belongs on every page of your application */


;
/*
  IIFE to control the glossary poppers.  See BK-4287.
*/
PBooksGlossary = (function($) {

    // This is a cache of ajax results, so that we don't do an ajax request twice
    // for two instances of the same glossary term.
    var popperTexts = {};

    // This stores the jQuery set of all glossary links on the page, so we only have
    // to find them once.
    var $glossaryLinks;
    // Same thing but as a set of DOM elements
    var glossaryLinks;

    /*
      The getGlossary function is called by JIG when the user hovers over a glossary
      item (see BK-4287).  Normally, it will do an ajax request to retrieve the
      glossary item, and will use asynchronous mode, invoking callback after the
      ajax request is done.  For glossary terms we've seen before, we'll use the cache,
      and will return immediately (synchronous mode).
    */
    var getGlossary = function(callback) {
        var href = $(this).attr('href');
        if (!href) return;  // not much we can do.

        // If we've already found a glossary item with this href, then use that
        if (popperTexts[href]) {
            return popperTexts[href];
        }

        // Otherwise, do an AJAX request, and store the result.
        var ajaxUrl = href + '?report=bare';
        $.ajax({
            url: ajaxUrl,
            success: function(data) {
                var bc = $(data).find('div.main-content');
                popperTexts[href] = bc;
                callback(bc);
            }
        });
    }



    /*
      Bind to an event that will fire from the "enable/disable glossary links"
      handler, in books.js.  This fires once on document ready, and once each time the user
      clicks on that control.
    */
    $('body').bind("glossarylinks", function() {
        // First time?  If so then find all the glossary links on the page
        if (typeof $glossaryLinks == "undefined") {
            $glossaryLinks = $('a.def');
            glossaryLinks = $glossaryLinks.get();
        }

        // If there are no glossary links, then there's nothing to do
        if ($glossaryLinks.length == 0) return;
        var $gl1 = $glossaryLinks.first();  // first one; use to determine our state

        // Are we enabling or disabling?
        var enabling = ! $gl1.hasClass('def_inactive');

        // Were they ever enabled before, or not?  This will be true if we have ever
        // stored off the popper options to data.popperopts
        var enabledBefore = $gl1.data.popperopts;

        // We'll enable the ncbipoppers on the links in batches, because sometimes there
        // can be thousands on a single page (e.g. NBK65951, see BK-4287).
        // The function doGlossLinkBatch() will do one batch, and then set a timeout
        // to re-invoke itself after a delay.
        var numGlossaryLinks = glossaryLinks.length;
        var batchSize = 100;
        var start = 0;
        function doGlossLinkBatch() {
            var end = Math.min(start + batchSize, numGlossaryLinks);
            //console.info("doGlossLinkBatch: start = " + start + ", end = " + end);
            
            for (var i = start; i < end; ++i) {
                $this = $(glossaryLinks[i]);

                // There are really only three cases: enabling for the first time, re-enabling,
                // or disabling.
   
                if (enabling && !enabledBefore) {      // enabling for the first time
                    // Instantiate and store the results
                    $this.ncbipopper({
                        destText: getGlossary,
                        hasArrow: true,
                        arrowDirection: "top",
                        width: "600px",
                        triggerPosition: "bottom left",
                        destPosition: "top left",
                        adjustFit: "autoAdjust",
                        //adjustFit: "none",
                        isTriggerElementCloseClick: false
                    });
                    $this.data.popperopts = $this.data('ncbipopper').options;
                }
        
                else if (enabling && enabledBefore) {       // re-enabling
                    $this.ncbipopper($this.data.popperopts);
                }
          
                else if (enabledBefore) {                   // disabling
                    $this.ncbipopper('destroy');
                }

            }
            
            
            start += batchSize;
            if (start < numGlossaryLinks) {
                window.setTimeout(doGlossLinkBatch, 1);
            }
        }
        
        // Kick off the first batch.
        doGlossLinkBatch();
        
    });

    /*
      This return makes the getGlossary function globally visible (as
      PBooksGlossary.getGlossary), in case we want to fix the HTML markup,
      as described above.
      For now, since we're setting the popper in the JS function above, this
      really isn't necessary.
      I also added popperTexts, to allow some debugging.
    */
    return {
        "getGlossary": getGlossary,
        "popperTexts": popperTexts
    };
})(jQuery);



;
// Pinger for video play button.  See BK-8000

if (typeof jQuery != "undefined") {
    (function($) {
        $(document).ready(function() {
        
            $('img[src="/corehtml/pmc/flowplayer/play-large.png"]').on('click', function() {
                if (ncbi && ncbi.sg && ncbi.sg.ping) {
                    ncbi.sg.ping({
                        "pagearea": "body",
                        "targetsite": "control",
                        "targetcat": "control",
                        "targettype": "video-play-button"
                    });
                }
            });
        
        });
    })(jQuery);
}
;
jQuery(function($) {
    // Set event listener to scroll the nav poppers to the current page when opened
    $("#source-link-top, #source-link-bottom").bind(
        "ncbipopperopencomplete",
        function() {
            var dest = $(this).attr('href');
            var selected_link = $(dest).find('.current-toc-entry');

            if (selected_link.length > 0) 
            {
                $(dest).scrollTo(selected_link, { offset: -100, duration:  400 });
            }
        }
    );  
});


;
/*
  The following is adapted from the "highlight" jQuery extension by Johann Burkard:
  <http://johannburkard.de/blog/programming/javascript/highlight-javascript-text-higlighting-jquery-plugin.html>
  
  Calling patterns:
  
    - Highlight the word "fleegle" wherever it appears in something with 
      class "content", using the default highlight-class "highlight":
          $('.content').highlight("fleegle");

    - Use a different class name for highlighting:
          $('.content').highlight("fleegle", {
              'highlight-class': 'term-highlight'
          });
  
  Options:
    - highlight-class:  string; class name to add to the <span> that
      marks matched text.
    - match-word:  boolean; default true.

  Original heading info:

    highlight v3
    Highlights arbitrary terms.
    <http://johannburkard.de/blog/programming/javascript/highlight-javascript-text-higlighting-jquery-plugin.html>
    
    MIT license.
    
    Johann Burkard
    <http://johannburkard.de>
    <mailto:jb@eaio.com>
*/

if (typeof(jQuery) != "undefined") {

    jQuery.fn.highlight = function(t, opts) {
        var term = t.toUpperCase();
        var defaults = {
            'highlight-class': 'highlight',
            'match-word': true
        }
        var options = jQuery.extend({}, defaults, opts);

        // The jQuery extension applies the function below to each 
        // jQuery object that matches the selector.
        return this.each(function() {
            innerHighlight(this, term);
        });

        // Here we define the function that does the work.  This highlights
        // all the occurrences of term within text node descendants of node.
        function innerHighlight(node, term) {
            // skip will be the return value.  It is set to one if we add a 
            // new <span> node.
            var skip = 0;
            
            // If this is a TEXT_NODE
            if (node.nodeType == 3) {
                // Find the pattern
                var re = options['match-word'] ? '\\b' + term + '\\b' : term; 
                var matchResult = node.data.toUpperCase().match(re);
                if (matchResult) {
                    var pos = matchResult.index;
                    
                    // Pattern was found, create a <span>
                    var spannode = document.createElement('span');
                    spannode.className = options['highlight-class'];
                    // splitText() creates two sibling DOM text nodes
                    // where there used to be one.
                    var middlebit = node.splitText(pos);
                    // After the next operation, we have three
                    var endbit = middlebit.splitText(term.length);
                    // Make a copy of the matched text node, and insert
                    // it into the span.
                    var middleclone = middlebit.cloneNode(true);
                    spannode.appendChild(middleclone);
                    // Replace the original matched text node with the span
                    middlebit.parentNode.replaceChild(spannode, middlebit);
                    skip = 1;
                }
            }
            
            // If this is an element that has children, and is not <script> or 
            // <style>, then recurse into the child nodes.
            else if (node.nodeType == 1 && 
                     node.childNodes && 
                     !/(script|style)/i.test(node.tagName)) 
            {
                for (var i = 0; i < node.childNodes.length; ++i) {
                    // Note the "i +=" in the next line.  If the current iteration of 
                    // innerHighlight causes a (span) node to be added, then we don't
                    // want to rerun innerHighlight on that.  We skip over it.
                    i += innerHighlight(node.childNodes[i], term);
                }
            }
            
            return skip;
        }
    };

    // This function is part of the original jQuery extension, but we dont' use it 
    // in PBooks, because there is no way (currently) of removing the highlighting.
    // If we do ever decide to implement that, then this could be improved by
    // just changing the class name, instead of putting the DOM back the way it was.
    
    jQuery.fn.removeHighlight = function() {
      return this.find("span.highlight").each(function() {
        this.parentNode.firstChild.nodeName;
        with (this.parentNode) {
          replaceChild(this.firstChild, this);
          normalize();
        }
      }).end();
    };
}



;
/*
  PBooksSearchTermHighlighter
  This drives the highlighting of search terms in a book part.
  It depends on a global JSON object named PBooksSearchTermData, which is
  dynamically generated, and contains the highlight color and the list of
  search terms that should be highlighted.
*/

   
if (typeof jQuery != "undefined" &&
    typeof jQuery.fn.highlight == "function" &&
    typeof PBooksSearchTermData != "undefined") 
{
    (function($) {

        // First check the date to see if the highlighting has expired or not.
        // If the search occurred on the same day as today, we'll highlight.
        var expired = true;   // assume expired.
        
        var searchDate = PBooksSearchTermData.dateTime;
        if (searchDate) {
            var da = searchDate.match(/(\d+)\/(\d+)\/(\d+)/);
            if (da && da[0]) {
                // "- 0" converts each of these into an integer.
                var searchDay = da[2] - 0;
                var searchMonth = da[1] - 0;
                var searchYear = da[3] - 0;

                var now = new Date();
                var nowDay = now.getDate();
                var nowMonth = now.getMonth() + 1;
                var nowYear = now.getFullYear();
                if (nowDay == searchDay &&
                    nowMonth == searchMonth &&
                    nowYear == searchYear) 
                {
                    expired = false;
                }
              /*
                console.info("searchDate = " + searchDate)
                console.info("search: day = " + searchDay + ", month = " + searchMonth + 
                             ", year = " + searchYear);
                console.info("current date/time is " + now);
                console.info("now:  day = " + nowDay + ", month = " + nowMonth + 
                             ", year = " + nowYear);
              */
            }
        }
        if (expired) { return; }



        // Let's first add a CSS rule to cause the highlighting to occur in the
        // right style.  The value of this is either "none", "bold", or a CSS
        // color name or numeric code.
        var highlighter = PBooksSearchTermData.highlighter;
        var highlightStyle;
        if (highlighter == "none") {
            highlightStyle = "";
        }
        else if (highlighter == "bold") { 
            highlightStyle = "font-weight: bold;";
        }
        else {
            highlightStyle = "background-color: " + highlighter + ";";
        }
        
        var style = 
            "<style type='text/css'>\n" +
            "  .term-highlight { " + highlightStyle + " }\n" +
            "</style>\n";
        $(style).appendTo("head");
        
        var main = $('div.main-content');
        var terms = PBooksSearchTermData.terms;
        for (var i = 0; i < terms.length; ++i) {
            main.highlight(terms[i], {
                'highlight-class': 'term-highlight'
            });
        }
    })(jQuery);
}
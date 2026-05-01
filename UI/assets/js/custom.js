(function ($) {
	
	"use strict";

	// Header Type = Fixed
  $(window).scroll(function() {
    var scroll = $(window).scrollTop();
    var box = $('.header-text').height();
    var header = $('header').height();

    if (scroll >= box - header) {
      $("header").addClass("background-header");
    } else {
      $("header").removeClass("background-header");
    }
  });

  var categoryConfig = {
    radio: {
      title: 'Radio Stations',
      description: 'Search or pick a station to begin streaming.',
      placeholder: 'Search radio stations...',
      items: [
        'https://radio.garden/listen/radio-one/abc:Radio One',
        'https://radio.garden/listen/classic-rock/xyz:Classic Rock',
        'https://radio.garden/listen/world-news/123:World News',
        'https://radio.garden/listen/electro-beats/456:Electro Beats',
        'https://radio.garden/listen/jazz-vibes/789:Jazz Vibes'
      ]
    },
    plane: {
      title: 'Flight Feeds',
      description: 'Search or pick a flight stream to monitor.',
      placeholder: 'Search flight feeds...',
      items: [
        'https://radio.garden/listen/flight-alpha/abc:Flight Alpha',
        'https://radio.garden/listen/flight-beta/xyz:Flight Beta',
        'https://radio.garden/listen/flight-gamma/123:Flight Gamma',
        'https://radio.garden/listen/flight-delta/456:Flight Delta',
        'https://radio.garden/listen/flight-epsilon/789:Flight Epsilon'
      ]
    },
    ship: {
      title: 'Ship Channels',
      description: 'Search or pick a maritime channel to track.',
      placeholder: 'Search ship channels...',
      items: [
        'https://radio.garden/listen/ship-aurora/abc:Ship Aurora',
        'https://radio.garden/listen/ship-beacon/xyz:Ship Beacon',
        'https://radio.garden/listen/ship-calm/123:Ship Calm',
        'https://radio.garden/listen/ship-drifter/456:Ship Drifter',
        'https://radio.garden/listen/ship-equinox/789:Ship Equinox'
      ]
    },
    satellite: {
      title: 'Satellite Feeds',
      description: 'Search or pick a satellite feed to inspect.',
      placeholder: 'Search satellite feeds...',
      items: [
        'https://radio.garden/listen/sat-zenith/abc:Sat Zenith',
        'https://radio.garden/listen/sat-orbit/xyz:Sat Orbit',
        'https://radio.garden/listen/sat-echo/123:Sat Echo',
        'https://radio.garden/listen/sat-aquila/456:Sat Aquila',
        'https://radio.garden/listen/sat-nova/789:Sat Nova'
      ]
    }
  };

  var activeCategory = null;

  function renderCategoryItems(category, filter) {
    var config = categoryConfig[category] || categoryConfig.radio;
    var query = (filter || '').toLowerCase();
    var results = [];

    config.items.forEach(function(item) {
      var parts = item.split(':');
      var url = parts[0];
      var name = parts[1] || url;

      if (!query || name.toLowerCase().indexOf(query) !== -1) {
        results.push({ url: url, name: name });
      }
    });

    if (!results.length) {
      $('.category-item-list').html('<li class="category-no-results">No items found.</li>');
      return;
    }

    var items = results.map(function(item) {
      return '<li class="category-item"><div class="category-meta"><span class="category-name">' + item.name + '</span><span class="category-url">' + item.url + '</span></div><button type="button" class="select-category-btn" data-url="' + item.url + '" data-category="' + category + '">Select</button></li>';
    });

    $('.category-item-list').html(items.join(''));
  }

  function openCategoryView(category) {
    activeCategory = category;
    var config = categoryConfig[category] || categoryConfig.radio;

    $('.category-title').text(config.title);
    $('.category-description').text(config.description);
    $('#category-search').attr('placeholder', config.placeholder).val('').focus();

    $('.category-home').hide();
    $('.category-view').removeClass('d-none').hide().fadeIn(200);
    renderCategoryItems(category);
  }

  function closeCategoryView() {
    $('.category-view').fadeOut(200, function() {
      $('.category-view').addClass('d-none');
      $('.category-home').fadeIn(200);
      activeCategory = null;
    });
  }

  $(document).on('click', '.category-launch', function(event) {
    event.preventDefault();
    var category = $(this).data('mode');
    openCategoryView(category);
  });

  $(document).on('click', '.back-button', function() {
    closeCategoryView();
  });

  $(document).on('input', '#category-search', function() {
    renderCategoryItems(activeCategory || 'radio', $(this).val());
  });

  $(document).on('click', '.select-category-btn', function() {
    var url = $(this).data('url');
    var category = $(this).data('category');
    console.log('selected:', category, url);
    // TODO: connect this URL to the Python API tooling for this category.
  });

  // Menu Accordion
  $(document).on('click', '.naccs .menu div', function() {
    var numberIndex = $(this).index();

    if (!$(this).hasClass('active')) {
      $('.naccs .menu div').removeClass('active');
      $('.naccs ul li').removeClass('active');

      $(this).addClass('active');
      $('.naccs ul').find('li:eq(' + numberIndex + ')').addClass('active');

      var listItemHeight = $('.naccs ul')
        .find('li:eq(' + numberIndex + ')')
        .innerHeight();
      $('.naccs ul').height(listItemHeight + 'px');
    }
  });

  // Menu Dropdown Toggle
  if ($('.menu-trigger').length) {
    $('.menu-trigger').on('click', function() {
      $(this).toggleClass('active');
      $('.header-area .nav').slideToggle(200);
    });
  }

  // Page loading animation
  $(window).on('load', function() {
    $('#js-preloader').addClass('loaded');
  });

})(window.jQuery);

    var items = results.map(function(item) {
      return '<li class="category-item"><div class="category-meta"><span class="category-name">' + item.name + '</span><span class="category-url">' + item.url + '</span></div><button type="button" class="select-category-btn" data-url="' + item.url + '" data-category="' + category + '">Select</button></li>';
    });

    $('.category-item-list').html(items.join(''));

  function openCategoryView(category) {
    activeCategory = category;
    var config = categoryConfig[category] || categoryConfig.radio;

    $('.category-title').text(config.title);
    $('.category-description').text(config.description);
    $('#category-search').attr('placeholder', config.placeholder).val('').focus();

    $('.category-home').hide();
    $('.category-view').removeClass('d-none').hide().fadeIn(200);
    renderCategoryItems(category);
  }

  function closeCategoryView() {
    $('.category-view').fadeOut(200, function() {
      $('.category-view').addClass('d-none');
      $('.category-home').fadeIn(200);
      activeCategory = null;
    });
  }

  $(document).on('click', '.category-launch', function(event) {
    event.preventDefault();
    var category = $(this).data('mode');
    openCategoryView(category);
  });

  $(document).on('click', '.back-button', function() {
    closeCategoryView();
  });

  $(document).on('input', '#category-search', function() {
    renderCategoryItems(activeCategory || 'radio', $(this).val());
  });

  $(document).on('click', '.select-category-btn', function() {
    var url = $(this).data('url');
    var category = $(this).data('category');
    console.log('selected:', category, url);
    // TODO: connect this URL to the Python API tooling for this category.
  });


  // Acc
    $(document).on("click", ".naccs .menu div", function() {
      var numberIndex = $(this).index();

      if (!$(this).is("active")) {
          $(".naccs .menu div").removeClass("active");
          $(".naccs ul li").removeClass("active");

          $(this).addClass("active");
          $(".naccs ul").find("li:eq(" + numberIndex + ")").addClass("active");

          var listItemHeight = $(".naccs ul")
            .find("li:eq(" + numberIndex + ")")
            .innerHeight();
          $(".naccs ul").height(listItemHeight + "px");
        }
    });

	// Menu Dropdown Toggle
  if($('.menu-trigger').length){
    $(".menu-trigger").on('click', function() { 
      $(this).toggleClass('active');
      $('.header-area .nav').slideToggle(200);
    });
  }


	// Page loading animation
	 $(window).on('load', function() {

        $('#js-preloader').addClass('loaded');
})(window.jQuery);
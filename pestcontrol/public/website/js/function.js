(function ($) {
	"use strict";

	var $window = $(window);
	var $body = $("body");

	/* Preloader Effect */
	$window.on("load", function () {
		$(".preloader").fadeOut(600);
	});

	/* Sticky Header */
	if ($(".active-sticky-header").length) {
		$window.on("resize", function () {
			setHeaderHeight();
		});

		function setHeaderHeight() {
			$("header.main-header").css("height", $("header .header-sticky").outerHeight());
		}

		$window.on("scroll", function () {
			var fromTop = $(window).scrollTop();
			setHeaderHeight();
			var headerHeight = $("header .header-sticky").outerHeight();
			$("header .header-sticky").toggleClass("hide", fromTop > headerHeight + 100);
			$("header .header-sticky").toggleClass("active", fromTop > 600);
		});
	}

	/* Slick Menu JS */
	$("#menu").slicknav({
		label: "",
		prependTo: ".responsive-menu",
	});

	if ($("a[href='#top']").length) {
		$(document).on("click", "a[href='#top']", function () {
			$("html, body").animate({ scrollTop: 0 }, "slow");
			return false;
		});
	}

	/* Hero Slider Layout JS */
	const hero_slider_layout = new Swiper(".hero-slider-layout .swiper", {
		effect: "fade",
		slidesPerView: 1,
		speed: 1000,
		spaceBetween: 0,
		loop: true,
		autoplay: {
			delay: 4000,
		},
		pagination: {
			el: ".hero-pagination",
			clickable: true,
		},
	});

	/* testimonial Slider JS */
	if ($(".testimonial-slider").length) {
		const testimonial_slider = new Swiper(".testimonial-slider .swiper", {
			slidesPerView: 1,
			speed: 1000,
			spaceBetween: 30,
			loop: true,
			autoplay: {
				delay: 5000,
			},
			pagination: {
				el: ".testimonial-pagination",
				clickable: true,
			},
			navigation: {
				nextEl: ".testimonial-btn-next",
				prevEl: ".testimonial-btn-prev",
			},
			breakpoints: {
				768: {
					slidesPerView: 2,
				},
				991: {
					slidesPerView: 3,
				},
			},
		});
	}

	/* Services Slider JS */
	if ($(".services-slider").length) {
		const services_slider = new Swiper(".services-slider .swiper", {
			slidesPerView: 1,
			speed: 1000,
			spaceBetween: 30,
			loop: true,
			autoplay: {
				delay: 5000,
			},
			pagination: {
				el: ".services-pagination",
				clickable: true,
			},
			breakpoints: {
				768: {
					slidesPerView: 2,
				},
				991: {
					slidesPerView: 4,
				},
			},
		});
	}

	/* Skill Bar */
	if ($(".skills-progress-bar").length) {
		$(".skills-progress-bar").waypoint(
			function () {
				$(".skillbar").each(function () {
					$(this)
						.find(".count-bar")
						.animate(
							{
								width: $(this).attr("data-percent"),
							},
							2000
						);
				});
			},
			{
				offset: "50%",
			}
		);
	}

	/* Init Counter */
	if ($(".counter").length) {
		$(".counter").counterUp({ delay: 6, time: 3000 });
	}

	/* Image Reveal Animation */
	if ($(".reveal").length) {
		gsap.registerPlugin(ScrollTrigger);
		let revealContainers = document.querySelectorAll(".reveal");
		revealContainers.forEach((container) => {
			let image = container.querySelector("img");
			let tl = gsap.timeline({
				scrollTrigger: {
					trigger: container,
					toggleActions: "play none none none",
				},
			});
			tl.set(container, {
				autoAlpha: 1,
			});
			tl.from(container, 1, {
				xPercent: -100,
				ease: Power2.out,
			});
			tl.from(image, 1, {
				xPercent: 100,
				scale: 1,
				delay: -1,
				ease: Power2.out,
			});
		});
	}

	/* Text Effect Animation */
	// SplitText breaks each element into individual char/word spans, which
	// corrupts Arabic letter-joining and ordering — skip it for RTL pages
	// and let the text render normally, unanimated.
	var isRTL = document.documentElement.dir === "rtl";

	if (!isRTL && $(".text-anime-style-1").length) {
		let staggerAmount = 0.05,
			translateXValue = 0,
			delayValue = 0.5,
			animatedTextElements = document.querySelectorAll(".text-anime-style-1");

		animatedTextElements.forEach((element) => {
			let animationSplitText = new SplitText(element, { type: "chars, words" });
			gsap.from(animationSplitText.words, {
				duration: 1,
				delay: delayValue,
				x: 20,
				autoAlpha: 0,
				stagger: staggerAmount,
				scrollTrigger: { trigger: element, start: "top 85%" },
			});
		});
	}

	if (!isRTL && $(".text-anime-style-2").length) {
		let staggerAmount = 0.03,
			translateXValue = 20,
			delayValue = 0.1,
			easeType = "power2.out",
			animatedTextElements = document.querySelectorAll(".text-anime-style-2");

		animatedTextElements.forEach((element) => {
			let animationSplitText = new SplitText(element, { type: "chars, words" });
			gsap.from(animationSplitText.chars, {
				duration: 1,
				delay: delayValue,
				x: translateXValue,
				autoAlpha: 0,
				stagger: staggerAmount,
				ease: easeType,
				scrollTrigger: { trigger: element, start: "top 85%" },
			});
		});
	}

	if (!isRTL && $(".text-anime-style-3").length) {
		let animatedTextElements = document.querySelectorAll(".text-anime-style-3");

		animatedTextElements.forEach((element) => {
			//Reset if needed
			if (element.animation) {
				element.animation.progress(1).kill();
				element.split.revert();
			}

			element.split = new SplitText(element, {
				type: "lines,words,chars",
				linesClass: "split-line",
			});
			gsap.set(element, { perspective: 400 });

			gsap.set(element.split.chars, {
				opacity: 0,
				x: "50",
			});

			element.animation = gsap.to(element.split.chars, {
				scrollTrigger: { trigger: element, start: "top 90%" },
				x: "0",
				y: "0",
				rotateX: "0",
				opacity: 1,
				duration: 1,
				ease: Back.easeOut,
				stagger: 0.02,
			});
		});
	}

	/* Parallaxie js */
	var $parallaxie = $(".parallaxie");
	if ($parallaxie.length && $window.width() > 991) {
		if ($window.width() > 768) {
			$parallaxie.parallaxie({
				speed: 0.55,
				offset: 0,
			});
		}
	}

	/* Zoom Gallery screenshot */
	$(".gallery-items").magnificPopup({
		delegate: "a",
		type: "image",
		closeOnContentClick: false,
		closeBtnInside: false,
		mainClass: "mfp-with-zoom",
		image: {
			verticalFit: true,
		},
		gallery: {
			enabled: true,
		},
		zoom: {
			enabled: true,
			duration: 300, // don't foget to change the duration also in CSS
			opener: function (element) {
				return element.find("img");
			},
		},
	});

	/* Contact form validation */
	var $contactform = $("#contactForm");
	$contactform.validator({ focus: false }).on("submit", function (event) {
		if (!event.isDefaultPrevented()) {
			event.preventDefault();
			submitForm();
		}
	});

	function submitForm() {
		/* Ajax call to submit form */
		$.ajax({
			type: "POST",
			url: "form-process.php",
			data: $contactform.serialize(),
			success: function (text) {
				if (text === "success") {
					formSuccess();
				} else {
					submitMSG(false, text);
				}
			},
		});
	}

	function formSuccess() {
		$contactform[0].reset();
		submitMSG(true, "Message Sent Successfully!");
	}

	function submitMSG(valid, msg) {
		if (valid) {
			var msgClasses = "h4 text-success";
		} else {
			var msgClasses = "h4 text-danger";
		}
		$("#msgSubmit").removeClass().addClass(msgClasses).text(msg);
	}
	/* Contact form validation end */

	/* Our Project (filtering) Start */
	$window.on("load", function () {
		if ($(".project-item-boxes").length) {
			/* Init Isotope */
			var $menuitem = $(".project-item-boxes").isotope({
				itemSelector: ".project-item-box",
				layoutMode: "masonry",
				masonry: {
					// use outer width of grid-sizer for columnWidth
					columnWidth: 1,
				},
			});

			/* Filter items on click */
			var $menudisesnav = $(".our-project-nav li a");
			$menudisesnav.on("click", function (e) {
				var filterValue = $(this).attr("data-filter");
				$menuitem.isotope({
					filter: filterValue,
				});

				$menudisesnav.removeClass("active-btn");
				$(this).addClass("active-btn");
				e.preventDefault();
			});
			$menuitem.isotope({ filter: "*" });
		}
	});
	/* Our Project (filtering) End */

	/* Our Blog (filtering) Start */
	$window.on("load", function () {
		if ($(".blog-item-boxes").length) {
			/* Init Isotope */
			var $blogmenuitem = $(".blog-item-boxes").isotope({
				itemSelector: ".blog-item-box",
				layoutMode: "masonry",
				masonry: {
					// use outer width of grid-sizer for columnWidth
					columnWidth: 1,
				},
			});

			/* Filter items on click */
			var $blogmenudisesnav = $(".our-blog-nav li a");
			$blogmenudisesnav.on("click", function (e) {
				var filterValue = $(this).attr("data-filter");
				$blogmenuitem.isotope({
					filter: filterValue,
				});

				$blogmenudisesnav.removeClass("active-btn");
				$(this).addClass("active-btn");
				e.preventDefault();
			});
			$blogmenuitem.isotope({ filter: "*" });
		}
	});
	/* Our Blog (filtering) End */

	/* Animated Wow Js */
	new WOW().init();

	/* Popup Video */
	if ($(".popup-video").length) {
		$(".popup-video").magnificPopup({
			type: "iframe",
			mainClass: "mfp-fade",
			removalDelay: 160,
			preloader: false,
			fixedContentPos: true,
		});
	}

	/* Careers (job openings filtering) */
	/*
	 * Deliberately not isotope, unlike the blog and project grids above.
	 * Those filter on one dimension through a CSS class; openings filter on
	 * department AND location at once, and isotope's masonry layout here is
	 * absolutely positioned with a left origin -- which lays out backwards
	 * under dir="rtl". Plain show/hide keeps normal document flow, so RTL
	 * needs no special casing, and it compares raw data- attribute values
	 * rather than the hashed class names css_class_for has to produce for
	 * arabic. With JS off, every card stays visible.
	 */
	if ($("[data-careers-grid]").length) {
		var $careersGrid = $("[data-careers-grid]");
		var $careersItems = $careersGrid.find(".careers-grid-item");
		var $careersFilters = $("[data-careers-filter]");
		var $careersCount = $("[data-careers-count]");
		var $careersNoMatch = $("[data-careers-no-match]");

		function applyCareersFilters() {
			var active = {};
			$careersFilters.each(function () {
				var value = $(this).val();
				if (value) {
					active[$(this).attr("data-careers-filter")] = value;
				}
			});

			var visible = 0;
			$careersItems.each(function () {
				var item = this;
				var matches = Object.keys(active).every(function (key) {
					return (item.dataset[key] || "") === active[key];
				});
				$(item).toggleClass("is-hidden", !matches);
				if (matches) {
					visible++;
				}
			});

			if ($careersNoMatch.length) {
				$careersNoMatch.prop("hidden", visible !== 0);
			}
			if ($careersCount.length) {
				$careersCount.text(
					($careersCount.attr("data-label-template") || "{n}").replace("{n}", visible)
				);
			}
		}

		$careersFilters.on("change", applyCareersFilters);
		applyCareersFilters();
	}

})(jQuery);

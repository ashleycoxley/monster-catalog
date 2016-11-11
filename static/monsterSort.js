$(document).ready(function() {
	$('select').change(function() {
		selection = $(this).val();
		if (selection == 'all') {
			$('.monster-box').show();
		} else {
			var selector = '.' + selection;
			if ($(selector)[0]) {
				$(selector).show();
				$(selector).siblings().hide();
			} else {
				$('.monster-box').hide();
			}
		}
	});
});

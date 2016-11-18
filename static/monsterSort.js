$(document).ready(function() {
	$('select').change(function() {
		selection = $(this).val();
		if (selection == 'all') {
			$('.monster-box').show();
		} else {
			var selector = '.' + selection;
			$('.monster-box').hide();
			$('.monster-box').filter(selector).show();
		}
	});
});
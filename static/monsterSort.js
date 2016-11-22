$(document).ready(function() {
	$('select').change(function() {
		selection = $(this).val();
		if (selection == 'all') {
			$('.monster-card').show();
		} else {
			var selector = '.' + selection;
			$('.monster-card').hide();
			$('.monster-card').filter(selector).show();
		}
	});
});
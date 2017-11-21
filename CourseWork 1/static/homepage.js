var slideIndex = 0;

function swapImages()
{
	slideIndex += 1;
	if (slideIndex > 2)
	{
		slideIndex = 0;
	}
	document.getElementById('imageGallery').src='/static/imageGallery/' + slideIndex + '.jpg';
	
	setTimeout(swapImages, 6000);
}
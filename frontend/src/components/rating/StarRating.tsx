import { useState } from 'react';

interface StarRatingProps {
  rating: number; // Average rating (0-5, can be decimal)
  count: number; // Number of ratings
  userRating?: number | null; // Current user's rating (1-5 or null)
  onRate?: (score: number) => Promise<void>; // Callback when user rates
  readOnly?: boolean; // Whether the rating is read-only
}

export default function StarRating({
  rating,
  count,
  userRating = null,
  onRate,
  readOnly = false,
}: StarRatingProps) {
  const [hoveredStar, setHoveredStar] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleClick = async (score: number) => {
    if (readOnly || !onRate || isSubmitting) return;

    setIsSubmitting(true);
    try {
      await onRate(score);
    } catch (error) {
      console.error('Failed to submit rating:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStar = (index: number) => {
    // Calculate how filled the star should be
    const displayRating = hoveredStar !== null ? hoveredStar : (userRating ?? rating);
    const fillPercentage = Math.max(0, Math.min(1, displayRating - index));

    const isInteractive = !readOnly && onRate;
    const isHovered = hoveredStar === index + 1;

    return (
      <button
        key={index}
        type="button"
        disabled={!isInteractive || isSubmitting}
        onMouseEnter={() => isInteractive && setHoveredStar(index + 1)}
        onMouseLeave={() => isInteractive && setHoveredStar(null)}
        onClick={() => handleClick(index + 1)}
        className={`relative transition-transform ${
          isInteractive ? 'cursor-pointer hover:scale-110' : 'cursor-default'
        } ${isSubmitting ? 'opacity-50' : ''}`}
        aria-label={`Rate ${index + 1} stars`}
      >
        {/* Background (empty star) */}
        <svg
          className="w-6 h-6 text-gray-600"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>

        {/* Foreground (filled star) */}
        <div
          className="absolute inset-0 overflow-hidden"
          style={{ width: `${fillPercentage * 100}%` }}
        >
          <svg
            className={`w-6 h-6 transition-colors ${
              isHovered
                ? 'text-yellow-300'
                : userRating && userRating >= index + 1
                ? 'text-yellow-500'
                : 'text-yellow-400'
            }`}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        </div>
      </button>
    );
  };

  return (
    <div className="flex flex-col gap-2">
      {/* Stars */}
      <div className="flex items-center gap-1">
        {[0, 1, 2, 3, 4].map(renderStar)}
      </div>

      {/* Rating info */}
      <div className="flex items-center gap-2 text-sm">
        <span className="text-gray-300">
          {rating.toFixed(1)} / 5.0
        </span>
        <span className="text-gray-500">
          ({count} {count === 1 ? '평가' : '평가'})
        </span>
      </div>

      {/* User rating status */}
      {userRating && (
        <div className="text-xs text-indigo-400">
          내 평가: {userRating}점
        </div>
      )}

      {/* Interactive hint */}
      {!readOnly && onRate && !userRating && (
        <div className="text-xs text-gray-500">
          별점을 클릭하여 평가하세요
        </div>
      )}
    </div>
  );
}

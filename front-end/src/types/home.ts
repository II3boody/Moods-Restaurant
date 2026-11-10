
export type Category = {
    id: number;
    name: string;
    name_ar: string | null;
    description: string | null;
    description_ar: string | null;
    image: string | null;
    sort_order: number;
    is_active: boolean;
    show_on_home: boolean;
    parent_id: number | null;
};

export type Product = {
    id: number;
    category_id: number;
    name: string;
    name_ar: string | null;
    description: string | null;
    description_ar: string | null;
    details: string | null;
    details_ar: string | null;
    price: number;
    image: string | null;
    is_popular: boolean;
    is_recommended: boolean;
    is_available: boolean;
};

export type HomeData = {
    categories: Category[];
    popular_products: Product[];
    recommended_products: Product[];
    best_sellers: Product[];
    offers: unknown[];
    festivals: unknown[];
    latest_reviews: unknown[];
    about: {
        story: string;
        story_ar: string | null;
        mission: string;
        mission_ar: string | null;
        address: string;
        phone: string;
        email: string;
        working_hours: string;
        facebook: string;
        instagram: string;
        map_embed_url: string;
    };
};
